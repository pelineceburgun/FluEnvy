from app.services.rag_service import RAGService

if __name__ == "__main__":
    rag = RAGService()
    count = rag.load_golden_dataset()
    print(f"Toplam yüklenen kayıt: {count}")