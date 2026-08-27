from nicegui import ui,app
from PIL import Image
import magic

app.native.window_args['resizable'] = False#关闭窗口调整
app.add_static_files('/static', 'static')#文件夹目录挂载


static_image = ["/static/wallpaper1.jpg","/static/【哲风壁纸】人物特写-动漫少女.jpg"]

sel = 0
wallpaper = static_image[sel]

scalenum = 150


def on_wheel(event):
    global sel
    global wallpaper
    delta = event.args.get('deltaY', 0)
    print(delta)
    L = len(static_image)
    if delta >0 :
        sel += 1
    else:
        sel -= 1
    print(sel)
    wallpaper = static_image[sel]


@ui.page('/')#主挂载
def index():
    ui.element("div").classes(f'fixed inset-0 -z-10 bg-[url("{wallpaper}")] bg-full bg-cover scale-{scalenum} blur-sm')
    with ui.element("div").classes('bg-cover absolute inset-0 flex items-center justify-center'):
        with ui.element("div").classes('w-[50%] h-[50vh] scale-[1.2] -translate-y-1/5 '):
            # with open(wallpaper,'rb') as f:
            #     file_data = f.read(2048)
            #     mime_type = magic.from_buffer(file_data, mime=True)
                # if mime_type == "video/mp4":
                #     print("video")
                #     ui.video(f"{wallpaper}")
                # else:
                img = ui.image(f"{wallpaper}").classes("h-auto rounded-2xl shadow-sm hover:-translate-y-3 hover:scale-[1.03] hover:shadow-2xl transition-all duration-300 ease-out cursor-pointer")
                img.on('wheel', on_wheel, throttle=0.05)



ui.run(native=True,reload=True,window_size=(1024, 576))