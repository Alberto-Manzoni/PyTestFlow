def init_dmm(address) :
    return dmm = NIDmm(address)

def measure_vref(dmm, avg_count=10) :
    reads = []
    for x in range(avg_count) :
        dmm.read_voltage()
        reads.append(dmm.read_voltage())
    read = np.mean(reads)self, name: str, steps: Iterable[Callable[[], State]]):
        
    return dmm.read_voltage()

from pytestflow import Sequence, flow
from pytestflow.core.states import PyTestflowPassed, PyTestflowFailed, step

@step()
def init_dmm(address) :
    return dmm = NIDmm(address)

@numeric_limit_step(limit=0.5, mode="ge")
def measure_vref(dmm, avg_count=10) :
    reads = []
    for x in range(avg_count) :
        dmm.read_voltage()
        reads.append(dmm.read_voltage())
    read = np.mean(reads)self, name: str, steps: Iterable[Callable[[], State]]):
        
    return dmm.read_voltage()