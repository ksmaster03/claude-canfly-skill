// ฟังก์ชันจังหวะสำหรับ draw(t) · ทุกตัวเป็นฟังก์ชันของเวลาล้วน (กระโดดไปเฟรมไหนก็ได้ผลเท่าเดิม)
// ใส่ในหน้าเว็บด้วย <script src="motionlib.js"> หรือ require() ใน node เพื่อทดสอบ
// สูตรเขียนใหม่จากสมการ (สปริงแบบปิด, สมการ Penner) ไม่ได้คัดลอกโค้ดจาก Remotion หรือ GSAP
(function(root){
const cl=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));

// สปริงแบบปิด: ค่าจาก 0 ไป 1 · zeta = อัตราหน่วง (<1 เด้งเกิน), w0 = ความถี่ธรรมชาติ (rad/วิ), t เป็นวินาที
function spring(t,zeta=0.6,w0=39.3){if(t<=0)return 0;
  if(zeta>=1)return 1-Math.exp(-w0*t)*(1+w0*t);
  const wd=w0*Math.sqrt(1-zeta*zeta);return 1-Math.exp(-zeta*w0*t)*(Math.cos(wd*t)+zeta*w0/wd*Math.sin(wd*t));}
// ตั้งสปริงจากสิ่งที่ตาเห็น: เกินเท่าไร (0.09 = 9%) และถึงจุดสูงสุดกี่วินาที
function springFrom(over=0.09,peak=0.10){const L=Math.log(over),zeta=-L/Math.sqrt(Math.PI*Math.PI+L*L);return{zeta,w0:Math.PI/(peak*Math.sqrt(1-zeta*zeta))};}
// คำเด้งขึ้น ค่าตั้งต้นวัดจากคลิปต้นแบบ: เกิน 9% ที่ 0.10 วิ นิ่งใน 0.2 วิ
const POP=springFrom(0.09,0.10);
const pop=(t)=>spring(t,POP.zeta,POP.w0);

// Penner / GSAP: u อยู่ระหว่าง 0 ถึง 1
const backOut=(u,s=1.70158)=>{u=cl(u)-1;return 1+(s+1)*u*u*u+s*u*u;};      // s 1.0 เกิน 3.7% · 1.70158 เกิน 10% · 2.5 เกิน 19%
const expoOut=(u)=>u>=1?1:1-Math.pow(2,-10*cl(u));                          // เลื่อนเข้า: เหลือระยะครึ่งหนึ่งทุกช่วงสั้นๆ
const expoIn=(u)=>u<=0?0:Math.pow(2,10*(cl(u)-1));                          // เลื่อนออก: เร่งขึ้นเรื่อยๆ
const powOut=(u,n=3)=>1-Math.pow(1-cl(u),n);
const powIn=(u,n=3)=>Math.pow(cl(u),n);
const inOut=(u,n=3)=>{u=cl(u);return u<0.5?Math.pow(2*u,n)/2:1-Math.pow(2*(1-u),n)/2;};
const steps=(t,fps=12)=>Math.floor(t*fps)/fps;                              // วาดท่า 12 ภาพ/วิ ในงานเรนเดอร์ 60

// เวลาเริ่มของชิ้นที่ i จาก n ชิ้น
//  each = ห่างคงที่ต่อชิ้น (คำเด้ง: 0.10–0.13 วิ) · amount = เวลารวมทั้งบรรทัด (ยาวเท่าเดิมไม่ว่ากี่ชิ้น)
//  from = 'start' | 'end' | 'center' | 'edges' · jitter = สุ่มแบบมี seed (0–1 ของ each)
function stagger(i,n,o={}){const each=o.amount!=null?o.amount/Math.max(1,n-1):(o.each??0.11);
  let k=i;if(o.from==='end')k=n-1-i;else if(o.from==='center')k=Math.abs(i-(n-1)/2);else if(o.from==='edges')k=(n-1)/2-Math.abs(i-(n-1)/2);
  const j=o.jitter?(hash(i,o.seed||1)-0.5)*o.jitter*each:0;return k*each+j;}
// กฎของ Manim สำหรับข้อความยาว: ยิ่งยาวยิ่งซ้อนกันมาก เวลารวมไม่บานปลาย
const lagRatio=(n)=>Math.min(4/Math.max(1,n),0.2);
function hash(i,s=1){const x=Math.sin(i*127.1+s*311.7)*43758.5453;return x-Math.floor(x);}

// ช่วงชีวิตของของหนึ่งชิ้นในช็อต: เข้า → ค้าง → ออกก่อนตัด · คืนค่า {in,out} อย่างละ 0..1
//  t0 = เวลาเข้า, t1 = เวลาตัดช็อต · dIn 0.3 กับ expoOut ให้ระยะที่เหลือ 149 69 32 15 7 px ต่อเฟรม (30fps)
//  ตรงกับต้นแบบที่วัดได้ 146 66 30 13 5 px (ตาเห็นว่าถึงที่ใน 0.2 วิ) · ขาออกวัดได้ 0.2 วิ
function life(t,t0,t1,dIn=0.3,dOut=0.2){return{in:expoOut((t-t0)/dIn),out:expoIn((t-(t1-dOut))/dOut)};}

// ตัวช่วยเบลอตามการเคลื่อนไหว: คืนรายการเวลาย่อยให้วาดซ้อนแล้วเฉลี่ย (ชัตเตอร์ 180° = ครึ่งเฟรม)
//  ที่ 60fps ชัตเตอร์ 180° เบลอแค่ 8 ms แทบไม่เห็น → ใช้ 270–360° หรือเปิดเฉพาะเฟรมที่ของเร็วสุด
function shutter(t,fps=60,angle=270,n=8){const span=angle/360/fps;return Array.from({length:n},(_,i)=>t-(i/n)*span);}

const api={cl,spring,springFrom,pop,POP,backOut,expoOut,expoIn,powOut,powIn,inOut,steps,stagger,lagRatio,hash,life,shutter};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.ML=api;
})(typeof window!=='undefined'?window:globalThis);
