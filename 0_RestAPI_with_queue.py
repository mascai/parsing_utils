import http.server
import socketserver
import os
import threading
import time

from queue import Queue


PORT = 8001


def run_parser(thread_id, person_id):
    threads_manager.active_threads.append(thread_id)
    print(f"{threading.current_thread().name} START {thread_id} {person_id}")
    time.sleep(15)
    print(f"{threading.current_thread().name} STOP {thread_id} {person_id}")
    
    threads_manager.on_thread_finished(thread_id, 123)
    

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ThreadsManager(metaclass=Singleton):
    def __init__(self):
        self.THREADS_NUM = 5
        self.person_ids = Queue()
        self.active_threads = []
        self.all_threads = [] # Threading object instances
    
    def new_thread(self, name, target, args, daemon):
        print("Call new_thread for name=", name)
        return MyThread(
            name=name,
            target=target,
            args=args,
            daemon=False,
            parent=self
        )
    
    def on_thread_finished(self, thread_id, data):
        """ Call when thread is finished"""
        print(f"Finish thread {thread_id}, {data}")
        self.active_threads.remove(thread_id)
        if not threads_manager.person_ids.empty():
            new_person_id = self.person_ids.get()
            print("on_thread_finished: parse=", new_person_id)
            process_person(new_person_id)
        else:
            print("Queue is empty")
    

    def get_free_thread_id(self):
        """ Get thread for a new task or None"""
        print(f"get_free_thread_id active_threads={self.active_threads}, self_id={id(self.active_threads)}")
        if len(self.active_threads) == 0:
            return 0
        for i in range(0, self.THREADS_NUM):
            if i not in self.active_threads:
                return i
        return None # no avaliable threads




class MyThread(threading.Thread):

    def __init__(self, name, target, args, daemon, parent=None):
        self.parent = parent
        super(MyThread, self).__init__(
            name=name,
            target=target,
            args=args,
            daemon=daemon
        )



def process_person(person_id):
    """Run thread with person parsing task"""
    thread_id = threads_manager.get_free_thread_id()
    print(f"process_person: thread_id={thread_id}, person_id={person_id}")
    if thread_id is not None:
        
        print(f"{threading.current_thread().name} QQQ_1", threads_manager.active_threads)

        thread_name = f"THREAD_{thread_id}"
        cur_thread = threads_manager.new_thread(
            name=thread_name,
            target=run_parser,
            args=((thread_id, person_id)),
            daemon=False
        )
        cur_thread.start()
        threads_manager.all_threads.append(cur_thread)
    else:
        print(f"Put person_id={person_id} to queue")
        threads_manager.person_ids.put(person_id)
        


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        print("LOG: Init MyHttpRequestHandler")        
        super().__init__(*args, directory=None, **kwargs)

    def do_GET(self):
        person_ids = self.path[1:].split(',')
        print("Handle request", person_ids)
        for person_id in person_ids:
            process_person(person_id)
        
        
threads_manager = ThreadsManager()

# Create an object of the above class
handler_object = MyHttpRequestHandler
my_server = socketserver.TCPServer(("", PORT), handler_object)

# Star the server
my_server.serve_forever()
