-- Enable the pgvector extension to work with embedding vectors
CREATE EXTENSION IF NOT EXISTS vector;

-- Create a table to store documents
CREATE TABLE documents (
  id uuid PRIMARY KEY,
  content text,         -- corresponds to Document.pageContent
  metadata jsonb,       -- corresponds to Document.metadata
  embedding vector(768) -- 768 works for google embeddings, change if needed
);


-- Create an index for better vector similarity search performance
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
-- `ivfflat` (Inverted File with Flat compression) is an approximate nearest neighbor (ANN) search algorithm.
-- Instead of comparing the query vector to *every* vector in the table, `ivfflat` divides the vectors into 
-- clusters and only compares the query vector to vectors within the most promising clusters. 
-- `vector_cosine_ops` specifies that the index should be optimized for cosine distance calculations

-- Create an index on metadata for faster filtering
CREATE INDEX idx_documents_metadata ON documents USING gin (metadata);
-- This creates an index on the `metadata` column using the `gin` (Generalized Inverted Index) method.
-- With the GIN index, the database can quickly locate the relevant rows
-- based on the filter criteria, avoiding a full table scan.

-- Create a function to search for documents
CREATE FUNCTION match_documents (
  query_embedding vector(768),
  match_count int DEFAULT 10,
  filter jsonb DEFAULT '{}'
) RETURNS TABLE (
  id uuid,
  content text,
  metadata jsonb,
  similarity float
) LANGUAGE plpgsql AS $$
#variable_conflict use_column
BEGIN
  RETURN QUERY
  SELECT
    id,
    content,
    metadata,
    1 - (documents.embedding <=> query_embedding) AS similarity
  FROM documents
  WHERE metadata @> filter
  ORDER BY documents.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

