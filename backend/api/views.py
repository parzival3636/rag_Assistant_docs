from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view
from rest_framework import status
from .models import Document
from .serializers import DocumentSerializer
from .services.processor import process_document
from .services.rag import answer_query
import logging
import os

logger = logging.getLogger(__name__)

# Handles file uploads
class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser]  # Accepts file uploads

    def post(self, request):
        logger.info("Document upload request received")
        
        # Check if file was provided
        if 'file' not in request.data:
            return Response(
                {"error": "No file provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file_obj = request.data['file']
        logger.info(f"Uploading file: {file_obj.name}, size: {file_obj.size}")
        
        # Check file type is supported
        allowed_extensions = ['.pdf', '.docx', '.txt']
        file_ext = os.path.splitext(file_obj.name)[1].lower()
        if file_ext not in allowed_extensions:
            return Response(
                {"error": f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create database record for the document
            doc = Document.objects.create(
                title=file_obj.name,
                file=file_obj,
                file_size=file_obj.size,
                file_type=file_ext[1:],  # Remove dot from extension
                status='P'  # Set status to Pending
            )
            logger.info(f"Document record created with ID: {doc.id}")
            
            # Process the document (extract text, chunk, embed)
            logger.info(f"Starting document processing for doc_id: {doc.id}")
            success, page_count = process_document(doc.file.path, doc.id)
            doc.page_count = page_count
            
            # Update status based on processing result
            doc.status = 'C' if success else 'F'  # Completed or Failed
            doc.save()
            
            if success:
                logger.info(f"Document {doc.id} processed successfully")
                return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)
            else:
                logger.error(f"Document {doc.id} processing failed")
                return Response(
                    {"error": "Document processing failed", "document": DocumentSerializer(doc).data},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        except Exception as e:
            logger.error(f"Error in document upload: {e}")
            return Response(
                {"error": f"Upload failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Lists all uploaded documents
@api_view(['GET'])
def list_documents(request):
    """Get list of all documents"""
    try:
        # Get all documents sorted by upload date (newest first)
        docs = Document.objects.all().order_by('-created_at')
        logger.info(f"Returning {docs.count()} documents")
        # Return serialized document data
        return Response(DocumentSerializer(docs, many=True).data)
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return Response(
            {"error": "Failed to list documents"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Handles questions about documents
@api_view(['POST'])
def query(request):
    """Answer questions about uploaded documents"""
    logger.info(f"Query request received: {request.data}")
    
    # Validate required fields
    question = request.data.get('question')
    doc_id = request.data.get('doc_id')
    
    if not question:
        return Response(
            {"error": "Question is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not doc_id:
        return Response(
            {"error": "Document ID is required"}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check document exists and is ready
    try:
        document = Document.objects.get(id=doc_id)
        if document.status != 'C':
            return Response(
                {"error": f"Document is not ready for queries. Status: {document.get_status_display()}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    except Document.DoesNotExist:
        return Response(
            {"error": "Document not found"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        # Process the question using RAG system
        logger.info(f"Processing query for doc_id: {doc_id}, question: {question}")
        result = answer_query(doc_id, question)
        
        # Add document info to response
        result['document'] = {
            'id': document.id,
            'title': document.title,
            'status': document.status
        }
        
        logger.info(f"Query processed successfully for doc_id: {doc_id}")
        return Response(result)
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return Response(
            {"error": f"Query processing failed: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )