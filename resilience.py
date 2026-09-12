"""Small, independently testable resilience demonstrations required by Part 4."""
import asyncio, random, time
class RetryPolicy:
    def __init__(self,max_attempts=5,initial=0.05,max_interval=0.2,jitter=0.01):
        self.max_attempts=max_attempts; self.initial=initial; self.max_interval=max_interval; self.jitter=jitter
def retry(fn,policy=RetryPolicy()):
    last=None
    for attempt in range(1,policy.max_attempts+1):
        try: return fn(attempt)
        except Exception as e:
            last=e
            if attempt==policy.max_attempts: raise
            delay=min(policy.max_interval,policy.initial*(2**(attempt-1)))+random.uniform(0,policy.jitter)
            time.sleep(delay)
    raise last
def transient_demo():
    calls={"n":0}
    def work(attempt):
        calls["n"]+=1
        if calls["n"]<3: raise RuntimeError("simulated transient failure")
        return "success"
    result=retry(work)
    return {"result":result,"calls":calls["n"]}
async def node_timeout():
    try: await asyncio.wait_for(asyncio.sleep(.2),timeout=.05)
    except asyncio.TimeoutError: return "per-node timeout fired cleanly"
async def global_timeout():
    try: await asyncio.wait_for(asyncio.sleep(.3),timeout=.05)
    except asyncio.TimeoutError: return "global timeout fired and cancelled run"
if __name__=="__main__":
    print("retry:",transient_demo())
    print(asyncio.run(node_timeout()))
    print(asyncio.run(global_timeout()))
