
def protected(f):
    def wrapped(*args, **kwargs):
        # verify token
        # cancel access when the token is not working
        
        return 0
    
    return wrapped

def tracker(f):
    def wrapped(*args, **kwargs):
        
        # track status of the thread
        # log errors 
        return 0
    
    return wrapped