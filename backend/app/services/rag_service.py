import os
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import json
from typing import List, Dict

_CHROMA_DIR = os.getenv("CHROMA_DIR", "./chroma_db")
_GOLDEN_DATASET_PATH = os.getenv("GOLDEN_DATASET_PATH", "./data/golden_dataset.json")

class RAGService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name="intfloat/e5-base-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

        self.vectorstore = Chroma(
            collection_name="golden_dataset",
            embedding_function=self.embeddings,
            persist_directory=_CHROMA_DIR
        )

    def load_golden_dataset(self, json_path: str = _GOLDEN_DATASET_PATH):
        """Golden Dataset'i ChromaDB'ye yükler"""
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            documents = []
            ids = []

            for idx, item in enumerate(data.get("golden_dataset", [])):
                content = f"""
Exam: {item.get('exam', 'Unknown')}
Task Type: {item.get('task_type', 'Unknown')}
Prompt: {item.get('prompt', '')[:500]}...
Quality: {item.get('quality', '')}
Score Level: {item.get('score_level', '')}
Student Text: {item.get('student_text', '')[:600]}...
"""

                doc = Document(
                    page_content=content.strip(),
                    metadata={
                        "id": item.get("id", f"doc_{idx}"),
                        "exam": item.get("exam"),
                        "task_type": item.get("task_type"),
                        "quality": item.get("quality")
                    }
                )
                documents.append(doc)
                ids.append(f"doc_{idx}")

            self.vectorstore.add_documents(documents, ids=ids)
            print(f"✅ Başarıyla {len(documents)} golden dataset kaydı ChromaDB'ye yüklendi.")
            return len(documents)

        except FileNotFoundError:
            print(f"❌ Dosya bulunamadı: {json_path}")
            print("   → Lütfen data/golden_dataset.json dosyasını oluşturun veya yolu kontrol edin.")
            return 0
        except Exception as e:
            print(f"❌ Hata oluştu: {e}")
            return 0

    def retrieve_similar_examples(self, query: str, exam: str = None, k: int = 5):
        """Öğrenci metnine benzer örnekleri getirir"""
        filter_dict = {"exam": exam} if exam else None
        
        results = self.vectorstore.similarity_search(query=query, k=k, filter=filter_dict)
        
        return [
            {
                "id": doc.metadata.get("id"),
                "content": doc.page_content[:1200],
                "metadata": doc.metadata
            }
            for doc in results
        ]