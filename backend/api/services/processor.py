import os
import pdfplumber
from docx import Document as DocxDocument
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import logging

# Set up logging to track what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize ChromaDB (vector database) and embedding model
try:
    # Connect to ChromaDB (stores our document chunks)
    client = chromadb.PersistentClient(path="E:/ragproj/chromadb_data")
    # Get or create collection for our documents
    collection = client.get_or_create_collection("documents")
    # Load sentence embedding model (converts text to numbers)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("Document processor initialized successfully")
except Exception as e:
    logger.error(f"Error initializing document processor: {e}")
    raise

def extract_text(file_path):
    """Get text from PDF, DOCX or TXT files and count pages"""
    logger.info(f"Extracting text from: {file_path}")

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        # Handle PDF files
        if file_path.lower().endswith('.pdf'):
            with pdfplumber.open(file_path) as pdf:
                text_parts = []
                # Go through each page and extract text
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                text = '\n'.join(text_parts)
                logger.info(f"Extracted {len(text)} characters from PDF")
                return text, len(pdf.pages)  # Return text + page count

        # Handle Word documents
        elif file_path.lower().endswith('.docx'):
            doc = DocxDocument(file_path)
            text_parts = []
            # Get text from each paragraph
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            text = '\n'.join(text_parts)
            logger.info(f"Extracted {len(text)} characters from DOCX")
            # Estimate pages (500 words per page)
            page_count = max(1, len(text.split()) // 500)
            return text, page_count

        # Handle plain text files
        elif file_path.lower().endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            logger.info(f"Extracted {len(text)} characters from TXT")
            # Estimate pages (500 words per page)
            page_count = max(1, len(text.split()) // 500)
            return text, page_count

        else:
            raise ValueError(f"Unsupported file format: {file_path}")

    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {e}")
        raise

def chunk_text(text, chunk_size=800, overlap=100):
    """Split long text into smaller pieces with some overlap"""
    if not text or not text.strip():
        logger.warning("Empty text provided for chunking")
        return []

    text = text.strip()
    # Split text into sentences
    sentences = text.replace('\n', ' ').split('. ')

    chunks = []
    current_chunk = ""

    # Build chunks by adding sentences until size limit
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Keep some overlap between chunks
            words = current_chunk.split()
            overlap_words = words[-overlap // 10:] if len(words) > overlap // 10 else words
            current_chunk = ' '.join(overlap_words) + ' ' + sentence
        else:
            current_chunk += sentence + '. '

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # Remove very small chunks
    chunks = [chunk for chunk in chunks if len(chunk.strip()) > 50]

    logger.info(f"Created {len(chunks)} chunks from text")
    return chunks

def process_document(file_path, doc_id):
    """Main function to process a document and store in database"""
    logger.info(f"Processing document {doc_id}: {file_path}")

    try:
        # Step 1: Extract text and count pages
        text, page_count = extract_text(file_path)
        if not text or len(text.strip()) < 10:
            logger.error(f"Extracted text is too short or empty for document {doc_id}")
            return False, page_count

        # Step 2: Split text into manageable chunks
        chunks = chunk_text(text)
        if not chunks:
            logger.error(f"No chunks created for document {doc_id}")
            return False, page_count

        # Step 3: Convert chunks to numerical embeddings
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        embeddings = model.encode(chunks).tolist()

        # Step 4: Prepare data for database
        chunk_ids = []
        documents = []
        metadatas = []
        chunk_embeddings = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Create unique ID for each chunk
            chunk_id = f"{doc_id}_{i}"
            chunk_ids.append(chunk_id)
            documents.append(chunk)
            # Store metadata about each chunk
            metadatas.append({
                "doc_id": str(doc_id),
                "chunk_index": i,
                "chunk_length": len(chunk)
            })
            chunk_embeddings.append(embedding)

        # Step 5: Store in ChromaDB
        try:
            # Delete old chunks if this document was processed before
            existing = collection.get(where={"doc_id": str(doc_id)})
            if existing['ids']:
                logger.info(f"Deleting {len(existing['ids'])} existing chunks for document {doc_id}")
                collection.delete(where={"doc_id": str(doc_id)})

            # Add new chunks to database
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=chunk_ids,
                embeddings=chunk_embeddings
            )

            logger.info(f"Successfully stored {len(chunk_ids)} chunks for document {doc_id}")
            # Verify data was stored correctly
            verification = collection.get(where={"doc_id": str(doc_id)})
            logger.info(f"Verification: {len(verification['ids'])} chunks found in database")

            return True, page_count

        except Exception as chroma_error:
            logger.error(f"ChromaDB storage error for document {doc_id}: {chroma_error}")
            return False, page_count

    except Exception as e:
        logger.error(f"Error processing document {doc_id}: {e}")
        return False, 0