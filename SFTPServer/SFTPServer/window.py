# This program is to generate a Server Start Screen
#   which connects connect to client and act as Remote Server

import logging
import threading
import socket
import time
import paramiko
import os

from tkinter import *
from stubserver import StubServer, StubSFTPServer
from datetime import datetime


Host, Port = socket.gethostbyname(socket.gethostname()), 22
KeyFile = 'test_rsa.key'
ON = True


def get_path(filename):
    root_path = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(root_path, filename)


def Message(Cmd):
    Output.configure(cursor="arrow", state=NORMAL)
    Output.insert(END, "\n"+str(Cmd))
    Output.see('end')
    Output.configure(cursor="arrow", state=DISABLED)


class TextHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        msg = self.format(record)
        Message(datetime.now().strftime("%H:%M:%S") +
                " Info Server: " + msg)

##################################  Graphical User Interface  #####################################


class Server:
    def __init__(self):
        self.window = Tk()
        self._setup_main_window()

    def run(self):
        self.window.mainloop()

    def _setup_main_window(self):
        self.window.geometry("700x500")
        self.window.title("Maxwell SFTP Server")
        self.window.configure(bg="#ffffff")
        self.window.resizable(False, False)
        icon = PhotoImage(file=f"Logo.png")
        self.window.iconphoto(False, icon)

        self.Host, self.Port = socket.gethostbyname(socket.gethostname()), 22
        self.Username, self.Password = "tester", "1234"
        self.UserDirectory = os.path.dirname(os.path.realpath(__file__))

        # Create Canvas
        self.canvas = Canvas(self.window, bg="#ffffff", height=500, width=700,
                             bd=0, highlightthickness=0, relief="ridge")
        self.canvas.place(x=0, y=0)

        # Button Widget
        self.img0 = PhotoImage(file=f"Start.png")
        self.b0 = Button(image=self.img0, borderwidth=0, highlightthickness=0,
                         command=self.Start_Clicked, relief="flat")
        self.b0.place(x=26, y=189, width=150, height=39)

        # Background Image

        self.background_img = PhotoImage(file=f"ServerBackground.png")
        self.background = self.canvas.create_image(
            349.5, 251.0, image=self.background_img)

        # Logo Design
        self.logo_img = PhotoImage(file=f"Logo.png")
        self.logo = self.canvas.create_image(102.5, 85.5, image=self.logo_img)

        # Message Widget for Details of Server
        self.Msg = Text(self.window, bg='#C4C4C4',
                        font=('Times New Roman', 12))
        self.Msg.insert(END, "Maxwell SFTP Server\n\n")
        self.Msg.insert(END, f"Server IP:                    {self.Host}\n")
        self.Msg.insert(END, f"Server Port:                 {self.Port}\n")
        self.Msg.insert(
            END, f"User:                           {self.Username}\n")
        self.Msg.insert(END, f"Password:                   {self.Password}\n")
        self.Msg.insert(END, f"User Root Directory:  {self.UserDirectory}")
        self.Msg.place(x=204, y=33, width=462, height=208)
        self.Msg.configure(state=DISABLED)

        logging.basicConfig(filename='Maxwell_Server_Log.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logger = logging.getLogger()
        text_handler = TextHandler()
        logger.addHandler(text_handler)

        # Message Widget for Details of Process Behind
        global Output
        Output = Text(self.window, bg='#C4C4C4', font=('Times New Roman', 9))
        Output.place(x=50, y=274, width=608, height=208)
        scrollbar = Scrollbar(Output, orient=VERTICAL)
        scrollbar.pack(side=RIGHT, fill=Y)
        Output.insert(END, '''Press "Start" button to begin.\n''')
        Output.configure(cursor="arrow", state=DISABLED,
                         yscrollcommand=scrollbar.set)
        scrollbar.config(command=Output.yview)

    # Thread the server implementation

    def Start_Clicked(self):
        self.server = StartServer()
        self.img1 = PhotoImage(file=f"Stop.png")
        self.b0.config(image=self.img1, borderwidth=0, highlightthickness=0,
                       command=lambda: self.Stop_Clicked(), relief="flat")
        self.server.daemon = True
        self.server.start()

    def Stop_Clicked(self):
        self.b0.config(image=self.img0, borderwidth=0, highlightthickness=0,
                       command=lambda: self.Start_Clicked(), relief="flat")
        self.server.Finish()

############################## Server Implementation Using Paramiko ###############################


class StartServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        Message("Binding SFTP Server to port 22..")
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
            self.sock.bind((Host, Port))
            Message("Starting...")
            logging.info("Starting Server")
        except Exception as e:
            logging.info("**** Bind Failed: " + str(e))

        logging.info(f"Listening for Connections at Port {Port}")
        try:
            self.sock.listen(1)
        except Exception as e:
            logging.info("**** Listen Failed: " + str(e))
        logging.info("Server Started.")
        Message("SFTP server has started and is ready to accept connections.")
        self.event = threading.Event()

    def run(self):
        try:
            self.conn, addr = self.sock.accept()
        except Exception as e:
            logging.info("**** Accept Failed: " + str(e))

        host_key = paramiko.RSAKey.from_private_key_file(
            get_path(KeyFile))

        self.transport = paramiko.Transport(self.conn)
        self.transport.add_server_key(host_key)
        self.transport.set_subsystem_handler(
            'sftp', paramiko.SFTPServer, StubSFTPServer)

        self.server = StubServer()
        self.transport.start_server(self.event, server=self.server)
        self.Channel = self.transport.accept()
        while self.transport.is_active():
            time.sleep(5)

    def Finish(self):
        Message("Stopping...")
        logging.info("Stopping Server")
        logging.info(f"No longer listening for Connections at Port {Port}")
        logging.info("Server Stopped.")
        try:
            self.sock.close()
        except Exception as e:
            Message(e)
        try:
            if not self.transport.is_active():
                Message("Stopped.")
        except Exception as e:
            Message(e)


if __name__ == "__main__":
    S = Server()
    S.run()
