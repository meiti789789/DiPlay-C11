import struct,zipfile,re,hashlib
from pathlib import Path
root=Path('/home/ken/DiPlay-c11-wheel-bridge');src=root/'dist/r9-release/DiPlay-C11-0.2.21-c11.9.apk';out=root/'dist/r12-release';out.mkdir(exist_ok=True)
u16=lambda b,o:struct.unpack_from('<H',b,o)[0]
u32=lambda b,o:struct.unpack_from('<I',b,o)[0]
def patch(b):
 chunks=[];pos=u16(b,2);strings=[];changed=0;code=0
 while pos<len(b):
  typ,hs,sz=struct.unpack_from('<HHI',b,pos);c=bytearray(b[pos:pos+sz])
  if typ==1:
   count,styles,flags,start,styleStart=struct.unpack_from('<IIIII',c,8);utf8=flags&256
   def length(p,wide=False):
    v=u16(c,p) if wide else c[p];step=2 if wide else 1;mask=32768 if wide else 128
    return (((v&(mask-1))<<(15 if wide else 8))+(u16(c,p+step) if wide else c[p+step]),p+2*step) if v&mask else (v,p+step)
   def enc(v,wide=False):
    if wide:return struct.pack('<H',v) if v<32768 else struct.pack('<HH',32768|(v>>16),v&65535)
    return bytes([v]) if v<128 else bytes([128|(v>>8),v&255])
   data=bytearray();offsets=[]
   for i in range(count):
    p=start+u32(c,hs+4*i);n,p=length(p,not utf8)
    if utf8:n,p=length(p);s=bytes(c[p:p+n]).decode('utf-8')
    else:s=bytes(c[p:p+2*n]).decode('utf-16le')
    if s=='0.2.21-c11.9':s='0.2.21-c11.12';changed+=1
    strings.append(s);offsets.append(len(data));raw=s.encode('utf-8' if utf8 else 'utf-16le');chars=len(s.encode('utf-16le'))//2
    data.extend((enc(chars)+enc(len(raw))+raw+b'\0') if utf8 else (enc(chars,True)+raw+b'\0\0'))
   while len(data)%4:data.append(0)
   prefix=c[:start];struct.pack_into('<'+'I'*count,prefix,hs,*offsets)
   tail=c[styleStart:] if styleStart else b''
   struct.pack_into('<I',prefix,24,start+len(data) if styleStart else 0)
   c=prefix+data+tail;struct.pack_into('<I',c,4,len(c))
  elif typ==0x102:
   ast=u16(c,24);asz=u16(c,26);cnt=u16(c,28)
   for i in range(cnt):
    p=16+ast+i*asz;name=strings[u32(c,p+4)]
    if name=='versionCode':
     assert c[p+15] in (16,17);struct.pack_into('<I',c,p+16,40012);code+=1
  chunks.append(c);pos+=sz
 assert changed==1 and code==1,(changed,code)
 r=bytearray(b[:u16(b,2)])+b''.join(chunks);struct.pack_into('<I',r,4,len(r));return r
with zipfile.ZipFile(src) as z,zipfile.ZipFile(out/'unsigned.apk','w') as w:
 for i in z.infolist():
  if re.match(r'META-INF/(?:MANIFEST.MF|[^/]+\.(?:SF|RSA|DSA|EC))$',i.filename,re.I):continue
  b=z.read(i.filename);w.writestr(i,patch(b) if i.filename=='AndroidManifest.xml' else b)
print('Prepared version-only rollback; original APK SHA256:',hashlib.sha256(src.read_bytes()).hexdigest())
