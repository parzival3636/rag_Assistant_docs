import requests
from sentence_transformers import SentenceTransformer
import chromadb
import logging
from groq import Groq
import os

# Set up logging to track operations
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize ChromaDB and embedding model
try:
    # Connect to our vector database
    client = chromadb.PersistentClient(path="E:/ragproj/chromadb_data")
    # Get our documents collection
    collection = client.get_or_create_collection("documents")
    # Load model to convert text to vectors
    model = SentenceTransformer('all-MiniLM-L6-v2')
    logger.info("ChromaDB and SentenceTransformer initialized successfully")
except Exception as e:
    logger.error(f"Error initializing ChromaDB or SentenceTransformer: {e}")
    raise

# Setup Groq client for AI responses
try:
    groq_client = Groq(api_key="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")
    logger.info("Groq client initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Groq client: {e}")
    groq_client = None

def get_document_chunks_for_query(doc_id, question, max_chunks=15):
    """Find relevant document parts based on question"""
    
    # Check question type to decide how much content to retrieve
    question_lower = question.lower()
    
    # For requests needing the whole document
    if any(keyword in question_lower for keyword in [
        'entire document', 'whole document', 'complete document', 'full text',
        'all content', 'everything', 'summary', 'summarize', 'overview'
    ]):
        # Get ALL chunks from database
        all_chunks = collection.get(where={"doc_id": str(doc_id)})
        if all_chunks['documents']:
            return {
                'documents': [all_chunks['documents']],
                'metadatas': [all_chunks['metadatas']]
            }
    
    # For questions needing multiple answers (like lists)
    elif any(keyword in question_lower for keyword in [
        'mcq', 'multiple choice', 'questions', 'list', 'points', 'items',
        'examples', 'steps', 'procedures'
    ]):
        max_chunks = 20  # Get more chunks for complex questions
    
    # Regular semantic search - convert question to vector
    q_embedding = model.encode(question).tolist()
    # Find most similar document chunks
    results = collection.query(
        query_embeddings=[q_embedding],
        n_results=max_chunks,
        where={"doc_id": str(doc_id)}
    )
    
    return results

def answer_query(doc_id, question):
    """Generate answer to question using document content"""
    logger.info(f"Processing query for doc_id: {doc_id}, question: {question}")
    
    try:
        # 1. Check if document exists in database
        try:
            doc_results = collection.get(where={"doc_id": str(doc_id)})
            logger.info(f"Total chunks found for doc_id {doc_id}: {len(doc_results['ids'])}")
            
            if len(doc_results['ids']) == 0:
                logger.error(f"No chunks found for document ID: {doc_id}")
                return {"error": f"Document {doc_id} not found in vector database. Please re-upload the document."}
        
        except Exception as chroma_error:
            logger.error(f"ChromaDB access error: {chroma_error}")
            return {"error": "Vector database access failed"}

        # 2. Get relevant document parts
        try:
            results = get_document_chunks_for_query(doc_id, question)
            if not results['documents'][0]:
                return {"answer": "No relevant information found in the document for this question."}
            
            logger.info(f"Retrieved {len(results['documents'][0])} chunks for processing")
        except Exception as query_error:
            logger.error(f"ChromaDB query error: {query_error}")
            return {"error": "Failed to search document"}

        # 3. Combine chunks into context for AI
        context_parts = []
        for i, (text, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
            if text and text.strip():
                context_parts.append(f"[Chunk {meta.get('chunk_index', i)}]: {text.strip()}")
        
        context = "\n\n".join(context_parts)
        logger.info(f"Context prepared with {len(context_parts)} chunks, {len(context)} characters")

        # 4. Adjust response settings based on question type
        question_lower = question.lower()
        
        # For comprehensive requests, allow longer responses
        if any(keyword in question_lower for keyword in [
            'entire document', 'whole document', 'complete', 'full text', 'all content'
        ]):
            max_tokens = 4000  # Very long responses
            temperature = 0.1  # More deterministic
        elif any(keyword in question_lower for keyword in [
            'mcq', 'multiple choice', 'list', 'points', 'steps', 'examples'
        ]):
            max_tokens = 2000  # Long structured responses
            temperature = 0.2
        elif 'summary' in question_lower or 'summarize' in question_lower:
            max_tokens = 1500  # Comprehensive summaries
            temperature = 0.3
        else:
            max_tokens = 800   # Regular answers
            temperature = 0.3

        # 5. First try local AI (LM Studio)
        try:
            system_prompt = """You are a helpful AI assistant. Provide comprehensive, detailed answers based on the document chunks provided. 

IMPORTANT INSTRUCTIONS:
- If asked for MCQs, provide EXACTLY the number requested with complete questions and all answer options
- If asked for lists, provide complete lists with all relevant items
- If asked for the entire document or full text, provide comprehensive coverage
- If asked for summaries, be thorough and include all key points
- Always be complete and don't truncate your responses
- Use clear formatting and structure your responses well"""

            response = requests.post(
                "http://localhost:1234/v1/chat/completions",
                json={
                    "model": "mistral",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": f"""Document chunks:
{context}

Question: {question}

Provide a complete and comprehensive answer. Do not truncate or limit your response."""
                        }
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False
                },
                timeout=60  # Wait longer for big responses
            )
            response.raise_for_status()
            answer = response.json()['choices'][0]['message']['content']
            logger.info(f"LM Studio response received, length: {len(answer)}")
            return {
                "answer": answer,
                "sources": results['metadatas'][0],
                "context_used": len(context_parts),
                "response_length": len(answer),
                "model_used": "LM Studio"
            }

        except requests.exceptions.RequestException as lm_error:
            logger.warning(f"LM Studio failed, switching to Groq: {lm_error}")

        # 6. Fallback to Groq AI if local fails
        if groq_client:
            try:
                # Use bigger model for complex requests
                if any(keyword in question_lower for keyword in [
                    'mcq', 'multiple choice', 'entire document', 'complete', 'full text', 'all content'
                ]):
                    model_name = "llama3-70b-8192"  # More powerful model
                else:
                    model_name = "llama3-8b-8192"   # Faster model

                groq_prompt = f"""Based on the document chunks below, provide a comprehensive and complete answer to the question. 

IMPORTANT: 
- If asked for multiple choice questions, provide EXACTLY the number requested
- If asked for lists, provide complete lists
- If asked for the entire document content, be comprehensive
- Do not truncate or limit your response
- Be thorough and complete

Document chunks:
{context}

Question: {question}

Complete Answer:"""

                groq_response = groq_client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": groq_prompt}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                answer = groq_response.choices[0].message.content
                logger.info(f"Groq response received, length: {len(answer)}")
                return {
                    "answer": answer,
                    "sources": results['metadatas'][0],
                    "context_used": len(context_parts),
                    "response_length": len(answer),
                    "model_used": f"Groq {model_name}"
                }
            except Exception as groq_error:
                logger.error(f"Groq API error: {groq_error}")
        
        # 7. Final fallback - return raw context if AI fails
        logger.warning("Both LLM services failed, returning comprehensive context")
        
        # For full document requests, return all context
        if any(keyword in question_lower for keyword in [
            'entire document', 'whole document', 'complete', 'full text', 'all content'
        ]):
            return {
                "answer": f"Here is the complete document content:\n\n{context}",
                "sources": results['metadatas'][0],
                "context_used": len(context_parts),
                "model_used": "Direct Context (Full)"
            }
        else:
            # For other requests, return partial context
            return {
                "answer": f"Based on the document, here are the relevant sections:\n\n{context[:3000]}{'...' if len(context) > 3000 else ''}",
                "sources": results['metadatas'][0],
                "context_used": len(context_parts),
                "model_used": "Direct Context (Partial)"
            }

    except Exception as e:
        logger.error(f"Unexpected error in answer_query: {e}")
        return {"error": f"Query processing failed: {str(e)}"}