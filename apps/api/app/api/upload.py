from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import aiofiles
import uuid

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    if file.size and file.size > 10_000_000:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    ext = Path(file.filename).suffix
    filename = f"{uuid.uuid4()}{ext}"
    filepath = UPLOAD_DIR / filename

    async with aiofiles.open(filepath, "wb") as f:
        content = await file.read()
        await f.write(content)

    return {"filename": filename, "url": f"/uploads/{filename}"}


@router.get("/{filename}")
async def download_file(filename: str):
    filepath = UPLOAD_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath, filename=filename)


@router.delete("/{filename}")
async def delete_file(filename: str):
    filepath = UPLOAD_DIR / filename
    if filepath.exists():
        filepath.unlink()
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="File not found")