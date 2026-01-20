import pytest
import tempfile
from pathlib import Path

from mcpruntime.services.content_manager import ContentManager


@pytest.mark.asyncio
async def test_small_text_passthrough():
    with tempfile.TemporaryDirectory() as tmpdir:
        async with ContentManager(storage_path=tmpdir, max_tokens=1000) as cm:
            blocks = [{"type": "text", "text": "Hello world"}]
            result = await cm.process_content(blocks)
            assert len(result) == 1
            assert result[0]["text"] == "Hello world"


@pytest.mark.asyncio
async def test_large_text_chunking():
    with tempfile.TemporaryDirectory() as tmpdir:
        async with ContentManager(storage_path=tmpdir, max_tokens=10) as cm:
            large_text = "word " * 100
            blocks = [{"type": "text", "text": large_text}]
            result = await cm.process_content(blocks)
            assert len(result) == 1
            assert "[Reference:" in result[0]["text"]
            assert "[Content truncated:" in result[0]["text"]


@pytest.mark.asyncio
async def test_content_retrieval():
    with tempfile.TemporaryDirectory() as tmpdir:
        async with ContentManager(storage_path=tmpdir, max_tokens=10) as cm:
            large_text = "word " * 100
            blocks = [{"type": "text", "text": large_text}]
            result = await cm.process_content(blocks)

            import re
            match = re.search(r'\[Reference: ([a-f0-9-]+)\]', result[0]["text"])
            assert match is not None
            ref_id = match.group(1)

            content = cm.get_content(ref_id)
            assert content["type"] == "text"
            assert "word" in content["text"]


@pytest.mark.asyncio
async def test_image_storage():
    with tempfile.TemporaryDirectory() as tmpdir:
        async with ContentManager(storage_path=tmpdir, describe_images=False) as cm:
            blocks = [{"type": "image", "data": "base64data", "mimeType": "image/png"}]
            result = await cm.process_content(blocks)
            assert len(result) == 1
            assert "[Image:" in result[0]["text"]
            assert "[Reference:" in result[0]["text"]
