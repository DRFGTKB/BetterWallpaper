import magic

with open(r"/static/w2.mp4",'rb') as f:
    file_data = f.read(2048)
    mime_type = magic.from_buffer(file_data, mime=True)
    print(mime_type)


