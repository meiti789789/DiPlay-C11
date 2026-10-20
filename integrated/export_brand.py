"""Render the code-native Android vector into required PNG protocol assets, using Cairo.
The input is vector path geometry; no existing bitmap is read or modified.
"""
from pathlib import Path
import ctypes,re,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
c=ctypes.CDLL('libcairo.so.2');P=ctypes.c_void_p;D=ctypes.c_double;I=ctypes.c_int

def fn(name,args,result=None):
 f=getattr(c,'cairo_'+name);f.argtypes=args;f.restype=result;return f
surface_create=fn('image_surface_create',[I,I,I],P);create=fn('create',[P],P)
scale=fn('scale',[P,D,D]);translate=fn('translate',[P,D,D]);save=fn('save',[P]);restore=fn('restore',[P])
move=fn('move_to',[P,D,D]);line=fn('line_to',[P,D,D]);curve=fn('curve_to',[P,D,D,D,D,D,D])
close=fn('close_path',[P]);fill=fn('fill',[P]);color=fn('set_source_rgb',[P,D,D,D]);new_path=fn('new_path',[P])
write=fn('surface_write_to_png',[P,ctypes.c_char_p],I);destroy=fn('destroy',[P]);destroy_surface=fn('surface_destroy',[P])

def draw_path(ctx,data):
 tokens=re.findall(r'[MCLHVZ]|[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?',data)
 i=0;command=None;x=y=startx=starty=0.0;new_path(ctx)
 while i<len(tokens):
  if tokens[i] in 'MCLHVZ':
   command=tokens[i];i+=1
   if command=='Z':close(ctx);x,y=startx,starty;command=None;continue
  count={'M':2,'L':2,'H':1,'V':1,'C':6}.get(command)
  if count is None:raise ValueError('Unsupported vector command')
  values=list(map(float,tokens[i:i+count]));i+=count
  if command=='M':x,y=values;move(ctx,x,y);startx,starty=x,y;command='L'
  elif command=='L':x,y=values;line(ctx,x,y)
  elif command=='H':x=values[0];line(ctx,x,y)
  elif command=='V':y=values[0];line(ctx,x,y)
  elif command=='C':curve(ctx,*values);x,y=values[-2:]
 fill(ctx)

def render():
 a='{http://schemas.android.com/apk/res/android}'
 root=ET.parse(ROOT/'overlay/common/src/main/res/drawable/ic_carplay.xml').getroot()
 surface=surface_create(0,256,256);ctx=create(surface);scale(ctx,256/108,256/108)
 def node(e):
  save(ctx)
  if e.tag=='group':
   translate(ctx,float(e.get(a+'translateX',0)),float(e.get(a+'translateY',0)))
   scale(ctx,float(e.get(a+'scaleX',1)),float(e.get(a+'scaleY',1)))
  if e.tag=='path':
   rgb=e.get(a+'fillColor','#FFFFFF').lstrip('#')
   color(ctx,*[int(rgb[i:i+2],16)/255 for i in (0,2,4)])
   draw_path(ctx,e.get(a+'pathData'))
  for child in e:node(child)
  restore(ctx)
 try:
  node(root)
  out=ROOT/'overlay/common/src/main/res/raw';out.mkdir(parents=True,exist_ok=True)
  for name in ['ic_car_home.png','placeholder_icon.png']:
   path=out/name
   if write(surface,str(path).encode())!=0:raise RuntimeError('Cairo PNG export failed')
  print('Rendered both 256x256 PNG assets from the official-path vector.')
 finally:destroy(ctx);destroy_surface(surface)

if __name__=='__main__':render()
