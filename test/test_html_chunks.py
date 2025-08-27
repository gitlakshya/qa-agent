import sys
import logging
from pathlib import Path

# Ensure the project root is on sys.path for direct invocation of this test file
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.load_chunk import LoadandChunk

logger = logging.getLogger(__name__)

def test_html_chunk(dir, html_file):
    chunk = LoadandChunk()
    chunks = chunk.load_chunk_html(dir, html_file)
    logger.info("Loaded %d HTML chunks from %s/%s", len(chunks), dir, html_file)

test_html_chunk("Jira_CSV", "MR_HTML.html")