import threading
from abc import abstractmethod, ABCMeta
from six import add_metaclass
from queue import Queue
import weakref


@add_metaclass(ABCMeta)
class QueueDaemon(threading.Thread):
    owner = None

    def __init__(self, owner=None, args=(), kwargs=None):
        super(QueueDaemon, self).__init__(args=(), kwargs=None)
        if owner:
            self.owner = weakref.ref(owner)
        self.queue = Queue()
        self.daemon = True

    def run(self):
        print('Daemon starting...')
        while True:
            job = self.queue.get()
            if job is None:  # If you send `None`, the thread will exit.
                print('Daemon exiting...')
                return
            self.add(job)

    @abstractmethod
    def add(self, job):
        pass


class SQSDaemon(QueueDaemon):
    def __init__(self, owner=None, args=(), kwargs=None, sqs=None):
        super(SQSDaemon, self).__init__(args=(), kwargs=None)
        self.sqs = sqs

    def add(self, job):
        if isinstance(job, (list, tuple)):
            self.sqs.send_messages(Entries=[j.encode() for j in job])
        else:
            self.sqs.send_message(MessageBody=job.encode())