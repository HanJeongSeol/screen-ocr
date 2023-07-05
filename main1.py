import time
import threading
from tkinter import *
from pororo import Pororo
import numpy as np
import cv2
from PIL import ImageGrab
import socketio
import webbrowser
global cnt
cnt = 0

class MyClient:
    def __init__(self):
        self.sio = socketio.Client()
        self.headers = {'X-Forwarded-For': 'localhost'}
        self.sio.connect('http://localhost:3306',self.headers)
        self.user=None
        self.playlistId = None

        @self.sio.on('connect')
        def on_connect():
            print('서버 연결')
        
        @self.sio.on('check')
        def on_chek(data):
            print("서버로 전달한 데이터 확인 %s" % data)
        
        @self.sio.on('state')
        def on_state(data):
            print("소켓 연결 상태 : %s" %data)
        
        @self.sio.on('user')
        def on_state(data):
            print("연결된유저 : %s" %data)
            self.user = data

        @self.sio.on('playlist') 
        def on_state(data) :
            print("플레이리스트 아이디 : %s" % data)
            self.playlistId  = data

    def send_data(self,data):
        self.sio.emit('text', data)

    def disconnect(self):
        self.sio.disconnect()
            

class PororoOcr:
    def __init__(self, model: str = "brainocr", lang: str = "ko", **kwargs):
        self.model = model
        self.lang = lang
        self._ocr = Pororo(task="ocr", lang=lang, model=model, **kwargs)
        self.img_path = None
        self.ocr_result = {}

    def run_ocr(self, img_path: str, debug: bool = False):
        self.img_path = img_path
        self.ocr_result = self._ocr(img_path, detail=True)

        if self.ocr_result['description']:
            ocr_text = self.ocr_result["description"]
        else:
            ocr_text = "No text detected."

        if debug:
            self.show_img_with_ocr()

        return ocr_text

class ThreadTask() :
    def __init__(self, taskFunc) :
        self.__taskFunc_ = taskFunc
        self.__workerThread_ = None
        self.__isRunning_ = False

    def taskFunc(self) :
        return self.__taskFunc_

    def isRunning(self) :
        return self.__isRunning_ and self.__workerThread_.is_alive()
    
    def start(self) :
        if not self.__isRunning_ :
            self.__isRunning_ = True
            self.__workerThread_ = self.WorkerThread(self)
            self.__workerThread_.start()
            
    def stop(self) :
        self.__isRunning_ = False

    class WorkerThread(threading.Thread) :
        def __init__(self, threadTask) :
            threading.Thread.__init__(self)
            self.__threadTask_ = threadTask
            self.daemon = True

        def run(self) :
            try :
                self.__threadTask_.taskFunc()(self.__threadTask_.isRunning)
            except Exception as e : print(repr(e))
            self.__threadTask_.stop()

def captureWidget(my_client):
    class CaptureGUI :
        def __init__(self,master) :
            self.master = master
            master.geometry("430x420+800+400")
            master.attributes('-alpha',0.8)
            master.attributes('-topmost',1)
            master.bind("<Configure>", self.setSize)
            # self.user = user
            self.startButton = Button(self.master, text ="캡쳐시작", command=self.captureStart,anchor="center")
            self.startButton.pack(padx=5, pady=20)
            
            self.stopButton = Button(self.master, text ="정지", command=self.captureStop,anchor="center")
            self.stopButton.pack(padx=5, pady=20)

            self.captureTask = ThreadTask(self.capture)

        def setSize(self,event):
            time.sleep(0.001)

            global coordinate 
            coordinate = list()


            width = root.winfo_width()
            height = root.winfo_height()

            coordinate.append(root.winfo_rootx())
            coordinate.append(root.winfo_rooty())
            coordinate.append(coordinate[0] + width)
            coordinate.append(coordinate[1]+height)
            
            self.coordinate = coordinate

            head = '캡쳐영역' + ' ' + str(width) + ' x ' + str(height) + ' ' + str(coordinate[0]) + ' x ' + str(coordinate[1])
            root.title(head)

            time.sleep(0.01)

        def capture(self, isRunningFunc = None) :
            cap_coordinate = self.coordinate
            root.attributes('-alpha',0.8)
            root.geometry('100x300+100+100')
            root.update()
            global cnt
            poro_ocr = PororoOcr()
            # my_client = MyClient()
            # print("캡쳐안의 유저")
            # print(self.user)
            while True :
                startTime = time.time()
                try :
                    if not isRunningFunc() :
                        my_client.disconnect()
                        return
                except : pass
                pass
                cnt = cnt + 1
                time.sleep(1)
                img = ImageGrab.grab(cap_coordinate)
                frame = np.array(img)
                frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
                img_name = "image/talk%d_test.png" % cnt
                cv2.imwrite(img_name,frame)
                text = poro_ocr.run_ocr(img_path=img_name)
                my_client.send_data(text)
                endTine = time.time()
                print("소요시간 : " , endTine-startTime)

        def captureStart(self) :
            print("captureStart")
            self.captureTask.start()

        def captureStop(self) :
            print("captureStop")
            root.geometry("430x420+800+400")
            root.update()

            self.captureTask.stop()

    root = Tk()
    captureWidget = CaptureGUI(root)
    root.mainloop()

# 소켓과 일차적으로 유저 정보를 받아오는 통신을 진행. 유저 정보 및 플리 저장시킬 그룹 선택 값을 서버에서 받아온다.
def userCheck() :
            my_client = MyClient()
            while True :
                try :
                    if my_client.playlistId != None :
                        return captureWidget(my_client)
                except : pass
                pass

if __name__ == "__main__" :
    url = "http://localhost2:3000/"
    webbrowser.open(url)
    userCheck()
