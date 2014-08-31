#Name: Sarvesh Sadhoo
#UTA ID: 1000980763
#Server Program
#Import all the libraries to be used in the program
import wx
import socket
import threading
import sys

# Button definitions for the chat server UI
ID_START = wx.NewId()

# Notification event for thread completion in UI
EVT_RESULT_ID = wx.NewId()

# Dictionary used to as a hash table to keep track of all the users connected to server
clientList = {}

# ClientThread is the main thread that handle the server. It creates thread for every new connection.
class ClientThread(threading.Thread):
    lock = threading.Lock()
    # Initialise all the variable to be used in the Class ClientThread
    def __init__(self, channel, details, notify_window):
        self.channel = channel
        self.details = details
        self.username = ''
        threading.Thread.__init__(self)
        self._notify_window = notify_window

    # Runs in an infinite loop to to receive data from the Client connected
    def run(self):
        while 1:
            try:
                # Receive data
                data = self.channel.recv(1024)
            except socket.error, msg:
                if 'timed out' in msg:
                    continue

            # Allows client to register with server
            if 'internalloginname' in data:
                self.username = data.split()[1]
                msg = 'New client ' + self.username + ' Login...'
                for c in clientList:
                    clientList[c][0].send(msg)
                ClientThread.lock.acquire()

                self.channel.send("1. Connecting to an online user before sending message is mandatory\n")
                self.channel.send("2. Use '!' For Listing All Online Users\n")
                self.channel.send("3. Use '@ <Buddy Name>' To Connect With Other User\n")
                self.channel.send("4. Do Not Try to Connect To A Busy User\n")
                self.channel.send("--------------------------------------------------------------------")
                ClientThread.lock.release()
                clientList[self.username] = [self.channel]

            # Add buddy   toto respective users in the ClientList hash table
            elif data[0] == "@":
                buddy = data[1:]
                for user in clientList:
                    print "user",user
                    print "buddy",buddy
                    print "chutiya",clientList[user]
                    if buddy in clientList[user]:
                        self.channel.send("Sorry you cannot connect to the user as he is currently busy")
                        self.channel.send("You won't be able to send anymore message as you tried to connect to a buys user")
                        self.channel.send("Close your window & try again later !")
                        break
                    elif buddy not in clientList[user] and len(clientList[user])== 1:
                        print "2"
                        clientList[self.username].append(buddy)
                        self.channel.send("You are connected to: " + buddy)
                        print "New List", clientList
                        break

            # Request to list all online users
            elif data == '!':
                users = ' | '.join(user for user in clientList)
                ClientThread.lock.acquire()
                self.channel.send(users)
                ClientThread.lock.release()
            # Request to quit
            elif data == 'internalquit':
#                ClientThread.lock.acquire()
                user_quit = self.username
                for c in clientList:
                    print "hell", clientList[c]
                    clientList[c][0].send(self.username + ' Logout.')
                del clientList[self.username]
                print "After deleteing quit user from array", clientList
                for user in clientList:
                    if clientList[user][1] == user_quit:
                        del clientList[user][1]
                print "After deleting user from other user ", clientList
               # print "Deleted user", clientList
                break

            # Message to all or peer
            elif data:
                msg = '#[' + self.username + ']\t>> '
                print "MSG", msg
                data_sender = msg[msg.find("[")+1:msg.find("]")]
                print "Data_Send_BY", data_sender
                data_receiver = clientList[data_sender][1]
                print "Data Received_BY", data_receiver
                if data: wx.PostEvent(self._notify_window, ResultEvent('GET/'+self.username+'/'+ data+'/'+data_receiver+'/'+'Htttp1.1'+ '\n'))
                if data:
                    #c = data.split('>>>')
                    if len(clientList) >= 2:
                        for user in clientList:
                            if user == data_receiver:
                                print "There is match with sender and receiver"
                                receiver_socket = clientList[user][0]
                                receiver_socket.send(msg + data)
                                self.channel.send(msg + data)
                    elif c[0] in clientList:
                        ClientThread.lock.acquire()
                        #print "ClientList", clientList

                        clientList[c[0]][0].send(msg + c[1])
                        self.channel.send(msg + c[1])
                        ClientThread.lock.release()
                    else:
                        ClientThread.lock.acquire()
                        self.channel.send('User ' + c[0] + ' is not online')
                        ClientThread.lock.release()
                else:
                    for c in clientList:
                        ClientThread.lock.acquire()
                        clientList[c][0].send(msg + data)
                        ClientThread.lock.release()

        self.channel.close()

def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data

class WorkerThread(threading.Thread):
    """Worker Thread Class."""
    def __init__(self, notify_window):
        """Init Worker Thread Class."""
        threading.Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = 0
        self.clientThreads = []

        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def run(self):
        """Run Worker Thread."""
        HOST = '127.0.0.1'  # Symbolic name meaning all available interfaces
        PORT = 50091        # Arbitrary non-privileged port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        socket.setdefaulttimeout(0.100)
        wx.PostEvent(self._notify_window, ResultEvent('Listening on port '+ str(PORT) + '\n'))
        s.listen(5)
        while 1:
            channel, details = s.accept()
            wx.PostEvent(self._notify_window, ResultEvent('Got Connection from ' + str(details) + '\n'))
            newThread = ClientThread(channel, details, self._notify_window).start()
            self.clientThreads.append(newThread)
        #for t in clientThreads:
        #    t.join()
            
    def abort(self):
        """abort worker thread."""
        # Method for use by main thread to signal an abort
        self._want_abort = 1

# GUI Frame class that spins off the worker thread
class MainFrame(wx.Frame):
    """Class MainFrame."""
    def __init__(self, parent, id):
        """Create the MainFrame."""
        wx.Frame.__init__(self, parent, id, 'Chat Server')
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        st1 = wx.StaticText(panel, -1, 'System Log')
        hbox1.Add(st1, 1)
        bt1 = wx.Button(panel, ID_START, 'Start Server')
        bt2 = wx.Button(panel, wx.ID_EXIT, 'Exit')
        hbox1.Add(bt1,1, wx.LEFT, 10)
        hbox1.Add(bt2,1, wx.ALIGN_RIGHT | wx.RIGHT, 10)
        vbox.Add(hbox1, 0, wx.LEFT, 10)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.log  = wx.TextCtrl(panel, -1, style=wx.TE_MULTILINE)
        hbox2.Add(self.log, 1, wx.EXPAND)
        vbox.Add(hbox2, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.status = wx.StaticText(panel, -1, '')
        hbox3.Add(self.status, 1)
        vbox.Add(hbox3, 0, wx.BOTTOM, 10)

        panel.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON, self.OnStart, id=ID_START)
        self.Bind(wx.EVT_BUTTON, self.OnStop, id=wx.ID_EXIT)

        # Set up event handler for any worker thread results
        EVT_RESULT(self,self.OnResult)

        # And indicate we don't have a worker thread yet
        self.worker = None

    def OnStart(self, event):
        """Start Computation."""
        # Trigger the worker thread unless it's already busy
        if not self.worker:
            self.status.SetLabel('Server Starting')
            self.worker = WorkerThread(self)

    def OnStop(self, event):
        """Stop Computation."""
        # Flag the worker thread to stop if running
        if self.worker:
            self.status.SetLabel('Trying to abort computation')
            self.worker.abort()
        self.Close()
        sys.exit(0)

    def OnResult(self, event):
        """Show Result status."""
        if event.data is None:
            # Thread aborted (using our convention of None return)
            self.status.SetLabel('Computation aborted')
        else:
            self.log.AppendText(event.data)
        # In either event, the worker is done
        self.worker = None

class MainApp(wx.App):
    """Class Main App."""
    def OnInit(self):
        """Init Main App."""
        self.frame = MainFrame(None, -1)
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True

if __name__ == '__main__':
    app = MainApp(0)
    app.MainLoop()
