import os
import database

try:
    import faiss
    import torch
    from sentence_transformers import SentenceTransformer
    from transformers import pipeline
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

class RAGEngine:
    def __init__(self):
        self.embedder = None
        self.llm = None
        self.is_loaded = False # Саме ця змінна блокує завантаження при старті

    def load_models(self):
        """Ліниве завантаження моделей у відеопам'ять лише за потреби."""
        if not ML_AVAILABLE or self.is_loaded:
            return
            
        print("⏳ Ініціалізація ML-модуля (завантаження у VRAM)...")
        self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.llm = pipeline(
            "text-generation",
            model="Qwen/Qwen1.5-0.5B-Chat",
            device_map="auto",
            # Виправили попередження torch_dtype -> dtype
            dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )
        self.is_loaded = True
        print("✅ ML-моделі успішно завантажено в пам'ять!")

    def get_course_texts(self, course_id):
        db = database.load_db()
        texts = []
        for course in db.get("courses", []):
            if course["id"] == course_id:
                for mat in course.get("materials", []):
                    if mat["path"].endswith(".txt") and os.path.exists(mat["path"]):
                        with open(mat["path"], 'r', encoding='utf-8') as f:
                            texts.append(f.read())
        return texts

    def explain_error(self, course_id, question, student_answer, correct_answer):
        # 1. Перевірка статусу від Адміністратора
        if not database.get_ml_status():
            return "❌ [ШІ Вимкнено]: Адміністратор системи тимчасово вимкнув інтелектуальний модуль для економії ресурсів."

        # 2. Перевірка наявності бібліотек
        if not ML_AVAILABLE:
            return f"🤖 [Режим заглушки]: Ви помилилися. Правильна відповідь '{correct_answer}'."

        # 3. Завантажуємо моделі, якщо це перший виклик після увімкнення
        if not self.is_loaded:
            self.load_models()

        # 4. RAG-логіка
        raw_texts = self.get_course_texts(course_id)
        if not raw_texts:
            return "🤖 Викладач ще не завантажив текстові лекції (.txt) для цього курсу."

        chunks = []
        for text in raw_texts:
            paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 50]
            chunks.extend(paragraphs)

        if not chunks:
            return "🤖 Текстові файли курсу порожні."

        embeddings = self.embedder.encode(chunks, convert_to_numpy=True)
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)

        query = f"Питання: {question} Відповідь: {correct_answer}"
        query_vector = self.embedder.encode([query], convert_to_numpy=True)
        distances, indices = index.search(query_vector, k=1)
        best_chunk = chunks[indices[0][0]]

        prompt = (
            f"<|im_start|>system\nТи - викладач. Поясни студенту помилку на основі лекції. Відповідай українською. Почни з 'Ви помилилися, оскільки згідно з лекцією...'.<|im_end|>\n"
            f"<|im_start|>user\nЛекція: {best_chunk}\n\n"
            f"Питання: {question}\nСтудент обрав: {student_answer}\nПравильно: {correct_answer}\n"
            f"Поясни помилку 1-2 реченнями.<|im_end|>\n<|im_start|>assistant\n"
        )

        output = self.llm(
            prompt, 
            max_new_tokens=150, 
            temperature=0.1, 
            do_sample=True,
            return_full_text=False
        )
        
        explanation = output[0]['generated_text'].strip()
        return explanation

# Створюємо глобальний об'єкт рушія (але тепер його __init__ порожній і не вантажить відеокарту!)
engine = RAGEngine()

if __name__ == "__main__":
    print("Модуль готовий.")