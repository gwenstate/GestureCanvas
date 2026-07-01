import cv2
import numpy as np
import datetime
import math
import random
from collections import deque

class Canvas:
    def __init__(self, width=1280, height=720):
        self.width  = width
        self.height = height
        self.canvas = np.zeros((height, width, 3), dtype=np.uint8)

        self.draw_color  = (100, 220, 255)
        self.brush_size  = 8
        self.eraser_size = 45
        self.mode        = "draw"
        self.prev_x = self.prev_y = None

        self.tx = 0; self.ty = 0
        self.scale = 1.0; self.angle = 0.0

        self.glow_mode     = False
        self.mirror_mode   = False
        self.velocity_mode = False
        self.rainbow_mode  = False
        self.rainbow_hue   = 0

        self.history   = deque(maxlen=20)
        self.particles = []

        self.left_w   = 82
        self.right_x  = width - 110
        self.right_cx = self.right_x + 55

        self.palette = [
            (0,200,255),(0,80,255),
            (0,0,255),(150,0,255),
            (255,0,200),(255,0,80),
            (255,100,0),(255,200,0),
            (0,255,255),(0,255,150),
            (0,200,60),(150,255,0),
            (255,255,255),(180,180,180),
            (90,90,90),(20,20,60),
        ]
        self.active_color_idx = 0
        col_x = [22, 60]
        row_y  = [48 + i*44 for i in range(8)]
        self.color_centers = [(col_x[c], row_y[r])
                              for r in range(8) for c in range(2)]

        self.spec_x=10; self.spec_y=408
        self.spec_w=62; self.spec_h=240
        self.spec_active=False; self.current_hue=15

        self.tools = [
            {"name":"draw",  "label":"DRAW", "color":(100,220,255)},
            {"name":"erase", "label":"ERASE","color":(180,180,180)},
            {"name":"move",  "label":"MOVE", "color":(80,230,80)},
        ]
        self.tool_y = [58, 108, 158]

        self.toggles = [
            {"key":"glow_mode",    "label":"GLOW","color":(255,200,80)},
            {"key":"mirror_mode",  "label":"MIRR","color":(180,100,255)},
            {"key":"velocity_mode","label":"VEL", "color":(80,220,255)},
            {"key":"rainbow_mode", "label":"RNBW","color":(255,100,180)},
        ]
        self.toggle_y = [318, 360, 402, 444]

        self.brush_dec_y  = 205
        self.brush_disp_y = 242
        self.brush_inc_y  = 280
        self.undo_y  = 492
        self.clear_y = 538
        self.save_y  = 584

        self.hover_type    = None
        self.hover_idx     = -1
        self.hover_counter = 0
        self.hover_needed  = 20

        self._color_bar = self._bake_bar()

    def _bake_bar(self):
        bar = np.zeros((self.spec_h, self.spec_w, 3), dtype=np.uint8)
        for row in range(self.spec_h):
            hue = int(179*row/self.spec_h)
            hsv = np.uint8([[[hue,230,255]]])
            bgr = cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)[0][0]
            bar[row,:] = bgr
        return bar

    def in_left(self,x,y):  return x <= self.left_w+5
    def in_right(self,x,y): return x >= self.right_x-5
    def in_panel(self,x,y): return self.in_left(x,y) or self.in_right(x,y)

    def check_palette_hover(self, x, y):
        if not self.in_panel(x,y):
            self._reset_hover(); return False

        if self.in_left(x,y):
            for i,(cx,cy) in enumerate(self.color_centers):
                if abs(x-cx)<17 and abs(y-cy)<17:
                    def pick(i=i):
                        self.draw_color=self.palette[i]
                        self.active_color_idx=i
                        self.rainbow_mode=False
                        self.mode="draw"
                    return self._hover("color",i,pick)
            if (self.spec_x<=x<=self.spec_x+self.spec_w and
                    self.spec_y<=y<=self.spec_y+self.spec_h):
                ratio=(y-self.spec_y)/self.spec_h
                hue=int(179*ratio)
                hsv=np.uint8([[[hue,230,255]]])
                bgr=cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)[0][0]
                self.draw_color=(int(bgr[0]),int(bgr[1]),int(bgr[2]))
                self.active_color_idx=-1
                self.rainbow_mode=False
                self.mode="draw"
                self.current_hue=hue
                self.spec_active=True
                self._reset_hover(); return True
            self.spec_active=False

        if self.in_right(x,y):
            cx=self.right_cx
            for i,ty in enumerate(self.tool_y):
                if abs(y-ty)<24 and abs(x-cx)<46:
                    return self._hover("tool",i,
                        lambda i=i: setattr(self,"mode",self.tools[i]["name"]))
            if abs(y-self.brush_dec_y)<22 and abs(x-cx)<36:
                return self._hover("bdec",0,
                    lambda: setattr(self,"brush_size",max(2,self.brush_size-2)))
            if abs(y-self.brush_inc_y)<22 and abs(x-cx)<36:
                return self._hover("binc",0,
                    lambda: setattr(self,"brush_size",min(60,self.brush_size+2)))
            for i,(tog,ty) in enumerate(zip(self.toggles,self.toggle_y)):
                if abs(y-ty)<20 and abs(x-cx)<46:
                    def flip(k=tog["key"]): setattr(self,k,not getattr(self,k))
                    return self._hover("toggle",i,flip)
            if abs(y-self.undo_y)<22 and abs(x-cx)<46:
                return self._hover("undo",0,self.undo)
            if abs(y-self.clear_y)<22 and abs(x-cx)<46:
                return self._hover("action",0,self.clear)
            if abs(y-self.save_y)<22 and abs(x-cx)<46:
                return self._hover("action",1,self._save)

        self._reset_hover(); return False

    def _hover(self,ht,idx,cb):
        if self.hover_type==ht and self.hover_idx==idx:
            self.hover_counter+=1
        else:
            self.hover_type=ht; self.hover_idx=idx; self.hover_counter=0
        if self.hover_counter>=self.hover_needed:
            cb(); self.hover_counter=0
        return True

    def _reset_hover(self):
        self.hover_type=None; self.hover_idx=-1; self.hover_counter=0

    def draw_panel(self, frame):
        self._draw_left(frame)
        self._draw_right(frame)
        self._draw_hud(frame)
        return frame

    def _draw_left(self, frame):
        ov=frame.copy()
        cv2.rectangle(ov,(0,0),(self.left_w,self.height),(13,13,13),cv2.FILLED)
        cv2.addWeighted(ov,0.84,frame,0.16,0,frame)
        cv2.line(frame,(self.left_w,0),(self.left_w,self.height),(42,42,42),1)
        cv2.putText(frame,"COLOR",(8,20),cv2.FONT_HERSHEY_SIMPLEX,0.38,(65,65,65),1)
        cv2.line(frame,(6,27),(self.left_w-6,27),(30,30,30),1)

        for i,((cx,cy),color) in enumerate(zip(self.color_centers,self.palette)):
            r=13
            cv2.circle(frame,(cx,cy),r,color,cv2.FILLED)
            cv2.circle(frame,(cx,cy),r,(32,32,32),1)
            if i==self.active_color_idx and self.mode=="draw" and not self.rainbow_mode:
                cv2.circle(frame,(cx,cy),r+4,(255,255,255),2)
            if self.hover_type=="color" and self.hover_idx==i and self.hover_counter>0:
                ang=int(360*self.hover_counter/self.hover_needed)
                cv2.ellipse(frame,(cx,cy),(r+8,r+8),-90,0,ang,(255,255,255),2)

        cv2.line(frame,(6,self.spec_y-10),(self.left_w-6,self.spec_y-10),(30,30,30),1)
        cv2.putText(frame,"PICK",(22,self.spec_y-1),cv2.FONT_HERSHEY_SIMPLEX,0.34,(60,60,60),1)
        frame[self.spec_y:self.spec_y+self.spec_h,
              self.spec_x:self.spec_x+self.spec_w] = self._color_bar
        cv2.rectangle(frame,(self.spec_x-1,self.spec_y-1),
                      (self.spec_x+self.spec_w+1,self.spec_y+self.spec_h+1),(55,55,55),1)
        if self.active_color_idx==-1 and self.spec_active:
            ind_y=self.spec_y+int(self.current_hue/179*self.spec_h)
            cv2.line(frame,(self.spec_x+self.spec_w+2,ind_y),
                     (self.spec_x+self.spec_w+10,ind_y),(255,255,255),2)
        prev_y=self.spec_y+self.spec_h+28
        disp_c=self.draw_color if not self.rainbow_mode else self._rainbow()
        cv2.circle(frame,(41,prev_y),18,disp_c,cv2.FILLED)
        cv2.circle(frame,(41,prev_y),18,(70,70,70),1)

    def _sep(self,frame,y):
        cv2.line(frame,(self.right_x+8,y),(self.width-8,y),(32,32,32),1)

    def _lbl(self,frame,y,text):
        cx=self.right_cx
        tw=cv2.getTextSize(text,cv2.FONT_HERSHEY_SIMPLEX,0.38,1)[0][0]
        cv2.putText(frame,text,(cx-tw//2,y),cv2.FONT_HERSHEY_SIMPLEX,0.38,(55,55,55),1)

    def _btn(self,frame,y,label,color,h_type,h_idx):
        cx=self.right_cx
        ah=(self.hover_type==h_type and self.hover_idx==h_idx and self.hover_counter>0)
        cv2.rectangle(frame,(self.right_x+6,y-20),(self.width-6,y+20),
                      (30,30,30) if ah else (20,20,20),cv2.FILLED)
        cv2.rectangle(frame,(self.right_x+6,y-20),(self.width-6,y+20),
                      color if ah else (40,40,40),1)
        tw=cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,0.48,1)[0][0]
        cv2.putText(frame,label,(cx-tw//2,y+8),cv2.FONT_HERSHEY_SIMPLEX,0.48,color,1)
        if ah:
            ang=int(360*self.hover_counter/self.hover_needed)
            cv2.ellipse(frame,(cx,y),(46,22),-90,0,ang,color,2)

    def _draw_right(self, frame):
        ov=frame.copy()
        cv2.rectangle(ov,(self.right_x,0),(self.width,self.height),(13,13,13),cv2.FILLED)
        cv2.addWeighted(ov,0.88,frame,0.12,0,frame)
        cv2.line(frame,(self.right_x,0),(self.right_x,self.height),(42,42,42),1)
        cx=self.right_cx

        self._lbl(frame,20,"TOOLS")
        self._sep(frame,30)

        for i,(tool,ty) in enumerate(zip(self.tools,self.tool_y)):
            active=self.mode==tool["name"]
            ic=tool["color"]
            cv2.rectangle(frame,(self.right_x+6,ty-22),(self.width-6,ty+22),
                          (28,28,28) if active else (18,18,18),cv2.FILLED)
            cv2.rectangle(frame,(self.right_x+6,ty-22),(self.width-6,ty+22),
                          ic if active else (36,36,36),1)
            tw=cv2.getTextSize(tool["label"],cv2.FONT_HERSHEY_SIMPLEX,0.5,1)[0][0]
            cv2.putText(frame,tool["label"],(cx-tw//2,ty+8),
                        cv2.FONT_HERSHEY_SIMPLEX,0.5,
                        ic if active else (62,62,62),2 if active else 1)
            if self.hover_type=="tool" and self.hover_idx==i and self.hover_counter>0:
                ang=int(360*self.hover_counter/self.hover_needed)
                cv2.ellipse(frame,(cx,ty),(46,24),-90,0,ang,ic,2)

        self._sep(frame,182); self._lbl(frame,196,"BRUSH SIZE")

        dec_on=self.hover_type=="bdec" and self.hover_counter>0
        cv2.rectangle(frame,(self.right_x+8,self.brush_dec_y-20),
                      (self.width-8,self.brush_dec_y+20),
                      (26,26,26) if dec_on else (18,18,18),cv2.FILLED)
        tw=cv2.getTextSize("-",cv2.FONT_HERSHEY_SIMPLEX,1.0,2)[0][0]
        cv2.putText(frame,"-",(cx-tw//2,self.brush_dec_y+10),
                    cv2.FONT_HERSHEY_SIMPLEX,1.0,(130,130,130),2)
        if dec_on:
            cv2.ellipse(frame,(cx,self.brush_dec_y),(44,22),-90,0,
                        int(360*self.hover_counter/self.hover_needed),(160,160,160),2)

        disp_c=self._rainbow() if self.rainbow_mode else self.draw_color
        bs=max(4,min(24,self.brush_size//2))
        cv2.circle(frame,(cx,self.brush_disp_y),bs,disp_c,cv2.FILLED)
        cv2.putText(frame,str(self.brush_size),(cx-8,self.brush_disp_y+bs+16),
                    cv2.FONT_HERSHEY_SIMPLEX,0.4,(55,55,55),1)

        inc_on=self.hover_type=="binc" and self.hover_counter>0
        cv2.rectangle(frame,(self.right_x+8,self.brush_inc_y-20),
                      (self.width-8,self.brush_inc_y+20),
                      (26,26,26) if inc_on else (18,18,18),cv2.FILLED)
        tw=cv2.getTextSize("+",cv2.FONT_HERSHEY_SIMPLEX,1.0,2)[0][0]
        cv2.putText(frame,"+",(cx-tw//2,self.brush_inc_y+10),
                    cv2.FONT_HERSHEY_SIMPLEX,1.0,(130,130,130),2)
        if inc_on:
            cv2.ellipse(frame,(cx,self.brush_inc_y),(44,22),-90,0,
                        int(360*self.hover_counter/self.hover_needed),(160,160,160),2)

        self._sep(frame,298); self._lbl(frame,312,"FX")

        for i,(tog,ty) in enumerate(zip(self.toggles,self.toggle_y)):
            on=getattr(self,tog["key"])
            ic=tog["color"]
            bg=(int(ic[0]*0.14),int(ic[1]*0.14),int(ic[2]*0.14)) if on else (18,18,18)
            cv2.rectangle(frame,(self.right_x+6,ty-20),(self.width-6,ty+20),bg,cv2.FILLED)
            cv2.rectangle(frame,(self.right_x+6,ty-20),(self.width-6,ty+20),
                          ic if on else (36,36,36),1)
            tw=cv2.getTextSize(tog["label"],cv2.FONT_HERSHEY_SIMPLEX,0.5,1)[0][0]
            cv2.putText(frame,tog["label"],(cx-tw//2,ty+8),
                        cv2.FONT_HERSHEY_SIMPLEX,0.5,
                        ic if on else (58,58,58),2 if on else 1)
            if on:
                cv2.circle(frame,(self.width-12,ty),4,ic,cv2.FILLED)
            if self.hover_type=="toggle" and self.hover_idx==i and self.hover_counter>0:
                cv2.ellipse(frame,(cx,ty),(46,22),-90,0,
                            int(360*self.hover_counter/self.hover_needed),ic,2)

        self._sep(frame,468)
        self._btn(frame,self.undo_y,f"UNDO ({len(self.history)})",(100,180,255),"undo",0)
        self._btn(frame,self.clear_y,"CLEAR",(80,80,210),"action",0)
        self._btn(frame,self.save_y,"SAVE",(50,190,90),"action",1)

    def _draw_hud(self, frame):
        mc={"draw":self.draw_color if not self.rainbow_mode else self._rainbow(),
            "erase":(180,180,180),"move":(80,230,80)}[self.mode]
        mid_x=(self.left_w+self.right_x)//2
        cv2.circle(frame,(mid_x-30,16),5,mc,cv2.FILLED)
        cv2.putText(frame,self.mode.upper(),(mid_x-22,21),
                    cv2.FONT_HERSHEY_SIMPLEX,0.46,mc,1)
        if self.scale!=1.0:
            cv2.putText(frame,f"{self.scale:.1f}x",(mid_x+40,21),
                        cv2.FONT_HERSHEY_SIMPLEX,0.46,(170,170,170),1)

    def _rainbow(self):
        hsv=np.uint8([[[int(self.rainbow_hue),240,255]]])
        bgr=cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)[0][0]
        return (int(bgr[0]),int(bgr[1]),int(bgr[2]))

    def screen_to_canvas(self, x, y):
        cx,cy=self.width//2,self.height//2
        M=cv2.getRotationMatrix2D((cx,cy),self.angle,self.scale)
        M[0,2]+=self.tx; M[1,2]+=self.ty
        Mi=cv2.invertAffineTransform(M)
        pt=np.array([[[float(x),float(y)]]],dtype=np.float32)
        r=cv2.transform(pt,Mi)
        return int(r[0][0][0]),int(r[0][0][1])

    def get_transformed_canvas(self):
        cx,cy=self.width//2,self.height//2
        M=cv2.getRotationMatrix2D((cx,cy),self.angle,self.scale)
        M[0,2]+=self.tx; M[1,2]+=self.ty
        return cv2.warpAffine(self.canvas,M,(self.width,self.height))

    def draw(self, x, y):
        if self.in_panel(x,y): return
        if self.rainbow_mode:
            self.rainbow_hue=(self.rainbow_hue+2)%180
            color=self._rainbow()
        else:
            color=self.draw_color
        cx,cy=self.screen_to_canvas(x,y)
        if self.velocity_mode and self.prev_x is not None:
            spd=math.hypot(cx-self.prev_x,cy-self.prev_y)
            size=max(2,min(self.brush_size*2,int(self.brush_size*1.8-spd*0.5)))
        else:
            size=self.brush_size
        if self.prev_x is not None:
            cv2.line(self.canvas,(self.prev_x,self.prev_y),(cx,cy),color,size)
            if self.mirror_mode:
                cv2.line(self.canvas,(self.width-self.prev_x,self.prev_y),
                         (self.width-cx,cy),color,size)
        self.prev_x,self.prev_y=cx,cy
        if random.random()<0.4:
            self._spawn_particles(x,y,color)

    def erase(self, x, y):
        if self.in_panel(x,y): return
        cx,cy=self.screen_to_canvas(x,y)
        cv2.circle(self.canvas,(cx,cy),self.eraser_size,(0,0,0),cv2.FILLED)
        if self.mirror_mode:
            cv2.circle(self.canvas,(self.width-cx,cy),self.eraser_size,(0,0,0),cv2.FILLED)
        self.prev_x=self.prev_y=None

    def move_canvas(self,dx,dy): self.tx+=dx; self.ty+=dy
    def zoom_canvas(self,f): self.scale=max(0.2,min(5.0,self.scale*f))

    def stop_drawing(self):
        if self.prev_x is not None:
            self.history.append(self.canvas.copy())
        self.prev_x=self.prev_y=None

    def undo(self):
        if self.history: self.canvas=self.history.pop()

    def clear(self):
        self.history.append(self.canvas.copy())
        self.canvas=np.zeros((self.height,self.width,3),dtype=np.uint8)
        self.tx=self.ty=0; self.scale=1.0; self.angle=0.0

    def _save(self):
        fname=f"GestureCanvas_{datetime.datetime.now().strftime('%H%M%S')}.png"
        cv2.imwrite(fname,self.get_transformed_canvas())
        print(f"Saved: {fname}")

    def draw_cursor(self,frame,x,y):
        color=self._rainbow() if self.rainbow_mode else self.draw_color
        if self.mode=="erase":
            cv2.circle(frame,(x,y),self.eraser_size,(160,160,160),2)
        elif self.mode=="move":
            cv2.drawMarker(frame,(x,y),(80,255,80),cv2.MARKER_CROSS,36,2)
        else:
            cv2.circle(frame,(x,y),self.brush_size+4,color,2)
            cv2.circle(frame,(x,y),3,(255,255,255),cv2.FILLED)
        return frame

    def blend_with_camera(self,camera_frame):
        t=self.get_transformed_canvas()
        if self.glow_mode:
            blurred=cv2.GaussianBlur(t,(0,0),12)
            t=cv2.addWeighted(t,1.0,blurred,0.9,0)
        gray=cv2.cvtColor(t,cv2.COLOR_BGR2GRAY)
        _,mask=cv2.threshold(gray,5,255,cv2.THRESH_BINARY)
        mask_inv=cv2.bitwise_not(mask)
        bg=cv2.bitwise_and(camera_frame,camera_frame,mask=mask_inv)
        fg=cv2.bitwise_and(t,t,mask=mask)
        return cv2.add(bg,fg)

    def _spawn_particles(self,x,y,color):
        for _ in range(6):
            self.particles.append({
                'x':float(x),'y':float(y),
                'vx':random.uniform(-3,3),
                'vy':random.uniform(-4,-0.5),
                'life':1.0,'color':color
            })

    def update_particles(self,frame):
        alive = []
        for p in self.particles:
            p['life'] -= 0.07
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['vy'] += 0.18
            if p['life'] > 0:
                a = p['life']
                c = tuple(min(255, int(v * a)) for v in p['color'])
                r = max(1, int(4 * a))
                cv2.circle(frame, (int(p['x']), int(p['y'])), r, c, cv2.FILLED)
                alive.append(p)
        self.particles = alive