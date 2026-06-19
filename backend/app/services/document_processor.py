"""
Document Processor

Extracts text from PDF bytes page-by-page using pdfplumber, performs text
cleanup, recursive sentence-aware chunking with configurable overlap, and
sentence-level metadata extraction for risk classification.
"""

import re
import io
from typing import List, Dict, Any
import pdfplumber


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------
def clean_text(text: str) -> str:
    """Normalize whitespace and remove excessive blank lines."""
    if not text:
        return ""
    text = re.sub(r"[ \t]+", " ", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using a heuristic regex that respects
    common abbreviations (e.g., i.e., etc.).
    """
    pattern = re.compile(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s")
    sentences = pattern.split(text)
    return [s.strip() for s in sentences if s.strip()]


# ---------------------------------------------------------------------------
# Document Processor
# ---------------------------------------------------------------------------
class DocumentProcessor:
    """Static helper class for PDF extraction and chunking."""

    @staticmethod
    def extract_text_from_pdf(pdf_bytes: bytes) -> List[Dict[str, Any]]:
        """
        Extract text page-by-page from raw PDF bytes.

        Returns:
            List of dicts: [{"page_num": 1, "text": "..."}]
        """
        pages: List[Dict[str, Any]] = []
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        cleaned = clean_text(page_text)
                        if cleaned:
                            pages.append({"page_num": i + 1, "text": cleaned})
        except Exception as e:
            # Re-raise so the caller can handle malformed PDFs
            raise ValueError(f"PDF extraction failed: {e}") from e
        return pages

    @staticmethod
    def create_chunks(
        pages: List[Dict[str, Any]],
        chunk_size: int = 500,
        overlap: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Create overlapping text chunks from page-level text.

        Strategy:
        - Split each page by paragraphs (double newline).
        - Merge small paragraphs into the current chunk.
        - If a paragraph exceeds chunk_size, split by sentences
          and apply overlap.

        Returns:
            List of dicts: [{"text": "...", "metadata": {"page_num": 1}}]
        """
        chunks: List[Dict[str, Any]] = []

        for page in pages:
            page_num = page["page_num"]
            paragraphs = page["text"].split("\n\n")

            current_chunk: List[str] = []
            current_len = 0

            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue

                para_len = len(para)

                # Large paragraph → split by sentences
                if para_len > chunk_size:
                    # Flush accumulated text first
                    if current_chunk:
                        chunks.append({
                            "text": "\n\n".join(current_chunk),
                            "metadata": {"page_num": page_num},
                        })
                        current_chunk = []
                        current_len = 0

                    sentences = split_into_sentences(para)
                    for sent in sentences:
                        sent_len = len(sent)
                        if current_len + sent_len > chunk_size:
                            if current_chunk:
                                chunks.append({
                                    "text": " ".join(current_chunk),
                                    "metadata": {"page_num": page_num},
                                })
                            # Build overlap from the tail of the previous chunk
                            overlap_sents: List[str] = []
                            accumulated = 0
                            for prev in reversed(current_chunk):
                                if accumulated + len(prev) < overlap:
                                    overlap_sents.insert(0, prev)
                                    accumulated += len(prev)
                                else:
                                    break
                            current_chunk = overlap_sents + [sent]
                            current_len = (
                                sum(len(s) for s in current_chunk)
                                + len(current_chunk) - 1
                            )
                        else:
                            current_chunk.append(sent)
                            current_len += sent_len + 1
                else:
                    # Normal-size paragraph → accumulate
                    if current_len + para_len > chunk_size:
                        if current_chunk:
                            chunks.append({
                                "text": "\n\n".join(current_chunk),
                                "metadata": {"page_num": page_num},
                            })
                        current_chunk = [para]
                        current_len = para_len
                    else:
                        current_chunk.append(para)
                        current_len += para_len + 2  # +2 for \n\n separator

            # Flush final chunk for this page
            if current_chunk:
                chunks.append({
                    "text": "\n\n".join(current_chunk),
                    "metadata": {"page_num": page_num},
                })

        return chunks

    @staticmethod
    def get_sentences_with_metadata(
        pages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Extract all sentences across pages, mapping each to its source
        page number. Used for line-by-line risk clause classification.
        """
        all_sentences: List[Dict[str, Any]] = []
        for page in pages:
            page_num = page["page_num"]
            paragraphs = page["text"].split("\n\n")
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                for sent in split_into_sentences(para):
                    all_sentences.append({"text": sent, "page_num": page_num})
        return all_sentences
