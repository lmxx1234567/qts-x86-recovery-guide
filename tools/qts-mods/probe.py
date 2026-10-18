"""Bounded by the caller; no native ctypes code runs in the reconciler."""
from __future__ import print_function
import ctypes,json,sys,struct
ctypes.CDLL('/lib/libuLinux_ini.so',mode=ctypes.RTLD_GLOBAL)
h=ctypes.CDLL('/lib/libuLinux_hal.so')
mode=sys.argv[1]
if mode=='symbols':
    for name in sys.argv[2:]:getattr(h,name)
    print('{}')
elif mode=='sensors':
    h.HM_Get_Temperature.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.POINTER(ctypes.c_double)]
    h.HM_Get_Fan.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.POINTER(ctypes.c_int),ctypes.POINTER(ctypes.c_int)]
    out={'temperature':[],'fan':[]}
    for i in [0,5]:
        v=ctypes.c_double();r=h.HM_Get_Temperature(0,i,ctypes.byref(v));out['temperature'].append([r,v.value])
    for i in [0,1]:
        v=ctypes.c_int();s=ctypes.c_int();r=h.HM_Get_Fan(0,i,ctypes.byref(v),ctypes.byref(s));out['fan'].append([r,v.value])
    print(json.dumps(out))
elif mode=='cache':
    h.SE_Get_Cacheable_Port_Bitmap.argtypes=[ctypes.c_int,ctypes.POINTER(ctypes.c_uint)]
    v=ctypes.c_uint();r=h.SE_Get_Cacheable_Port_Bitmap(0,ctypes.byref(v));print(json.dumps({'rc':r,'mask':v.value}))
elif mode=='memory':
    h.HAL_MB_Mem_Get_Info.argtypes=[ctypes.c_int,ctypes.c_void_p]
    out=[]
    for i in range(1,int(sys.argv[2])+1):
        b=ctypes.create_string_buffer(4096);r=h.HAL_MB_Mem_Get_Info(i,b)
        out.append({'rc':r,'header':list(struct.unpack('6i',b.raw[:24]))})
    print(json.dumps(out))
else:raise ValueError('Unknown read-only probe')
