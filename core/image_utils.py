import base64

def to_data_url(image_bytes: bytes,mime_type: str = 'image/prg') -> str:
    b64 = base64.b64encode(image_bytes).decode('utf-8')
    return f'data:{mime_type};base64,{b64}'