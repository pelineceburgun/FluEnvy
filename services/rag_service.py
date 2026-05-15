from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
import json
from pathlib import Path

class RAGService:
    def __init__(self, persist_directory: str = "./chroma_db"):
        # Ücretsiz embedding modeli (multilingual)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",          # multilingual ve ücretsiz
            model_kwargs={'device': 'cpu'},    # GPU istiyorsan 'cuda'
            encode_kwargs={'normalize_embeddings': True}
        )
        
        self.vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings,
            collection_name="golden_dataset"
        )

    def load_golden_dataset(self, json_path: str = "data/golden_dataset.json"):
        """38 kayıtlı Golden Dataset'i yükler"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = []
        ids = []

        for idx, item in enumerate(data.get("golden_dataset", [])):
            content = f"""
Exam: {item.get('exam')}
Task Type: {item.get('task_type')}
Prompt: {item.get('prompt')}
Quality: {item.get('quality')}
Score Level: {item.get('score_level')}
Student Text: {item.get('student_text')}
Evaluation: {json.dumps(item.get('detailed_evaluation', {}))}
Error Tags: {json.dumps(item.get('error_tags', []))}
"""

            doc = Document(
                page_content=content.strip(),
                metadata={
                    "id": item["id"],
                    "exam": item.get("exam"),
                    "task_type": item.get("task_type"),
                    "quality": item.get("quality")
                }
            )
            documents.append(doc)
            ids.append(f"doc_{idx}")

        self.vectorstore.add_documents(documents, ids=ids)
        print(f"✅ {len(documents)} Golden Dataset kaydı ChromaDB'ye yüklendi (ücretsiz bge-m3 ile).")
        return len(documents)

    def retrieve_similar_examples(self, query: str, exam: str = None, k: int = 5):
        """Öğrenci metnine benzer örnekleri çeker"""
        filter_dict = {"exam": exam} if exam else None
        
        results = self.vectorstore.similarity_search(query=query, k=k, filter=filter_dict)
        
        examples = []
        for doc in results:
            examples.append({
                "example_id": doc.metadata.get("id"),
                "content": doc.page_content[:1800],   # token sınırı için
                "metadata": doc.metadata
            })
        return examples