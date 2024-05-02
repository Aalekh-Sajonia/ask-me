import os
import string
import random

def create_random_uid(size=16, chars=string.digits + string.ascii_uppercase):
    return ''.join(random.choice(chars) for _ in range(size))

def handle_uploaded_file(f, name):
    print("f", f)
    destination = os.path.join(os.path.dirname(os.path.dirname(__file__)),'assistant_app/uploaded_files/' + name + '.txt')
    with open(destination, "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return destination

