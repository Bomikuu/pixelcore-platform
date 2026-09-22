import json
import struct


MAX_TRIANGLES = 200_000
MAX_NODES = 500
MAX_MESHES = 200
MAX_MATERIALS = 100
MAX_TEXTURES = 100
MAX_ANIMATIONS = 50


def validate_glb(upload):
    """Return presentation-safe model metadata or a rejection reason."""
    upload.seek(0)
    header = upload.read(12)
    if len(header) != 12:
        return None, "The model is not a complete GLB file."
    magic, version, declared_length = struct.unpack("<4sII", header)
    if magic != b"glTF" or version != 2:
        return None, "Only binary glTF 2.0 (GLB) models are supported."
    if declared_length != upload.size:
        return None, "The GLB declared length does not match the uploaded file."
    chunk_header = upload.read(8)
    if len(chunk_header) != 8:
        return None, "The GLB is missing its JSON scene description."
    chunk_length, chunk_type = struct.unpack("<II", chunk_header)
    if chunk_type != 0x4E4F534A or chunk_length > upload.size - 20:
        return None, "The GLB JSON chunk is invalid."
    try:
        document = json.loads(upload.read(chunk_length).decode("utf-8").rstrip(" \t\r\n\x00"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "The GLB JSON scene description could not be read."

    for resource in [*(document.get("buffers") or []), *(document.get("images") or [])]:
        uri = resource.get("uri")
        if uri and not str(uri).startswith("data:"):
            return None, "The model references an external file. Upload one self-contained GLB."

    limits = {
        "nodes": MAX_NODES,
        "meshes": MAX_MESHES,
        "materials": MAX_MATERIALS,
        "textures": MAX_TEXTURES,
        "animations": MAX_ANIMATIONS,
    }
    for key, maximum in limits.items():
        if len(document.get(key) or []) > maximum:
            return None, f"The model has too many {key} for storefront display."

    accessors = document.get("accessors") or []
    triangles = 0
    for mesh in document.get("meshes") or []:
        for primitive in mesh.get("primitives") or []:
            accessor_index = primitive.get("indices")
            count = 0
            if isinstance(accessor_index, int) and 0 <= accessor_index < len(accessors):
                count = int(accessors[accessor_index].get("count") or 0)
            elif isinstance(primitive.get("attributes", {}).get("POSITION"), int):
                position_index = primitive["attributes"]["POSITION"]
                if 0 <= position_index < len(accessors):
                    count = int(accessors[position_index].get("count") or 0)
            mode = primitive.get("mode", 4)
            triangles += count // 3 if mode == 4 else max(0, count - 2)
    if triangles > MAX_TRIANGLES:
        return None, "The model exceeds the 200,000 triangle storefront limit."

    upload.seek(0)
    return {
        "glb_version": 2,
        "triangles": triangles,
        "nodes": len(document.get("nodes") or []),
        "meshes": len(document.get("meshes") or []),
        "materials": len(document.get("materials") or []),
        "animations": len(document.get("animations") or []),
    }, ""
