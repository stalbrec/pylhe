import awkward as ak
import vector

__all__ = ["register_awkward", "to_awkward","to_awkward_nanoaod"]


# Python 3.7+
def __dir__():
    return __all__


def register_awkward():
    """Register Awkwawrd behaviors for pylhe."""

    vector.register_awkward()
    ak.mixin_class(ak.behavior)(Particle)
    ak.mixin_class(ak.behavior)(Event)
    ak.mixin_class(ak.behavior)(EventInfo)


def to_awkward(event_iterable):
    """Convert iterarble of LHEEvents to Awkward-Array."""

    builder = ak.ArrayBuilder()
    for event in event_iterable:
        with builder.record(name="Event"):
            builder.field("eventinfo")
            with builder.record(name="EventInfo"):
                for fname in event.eventinfo.fieldnames:
                    builder.field(fname).real(getattr(event.eventinfo, fname))
            builder.field("particles")
            with builder.list():
                for particle in event.particles:
                    with builder.record(name="Particle"):
                        builder.field("vector")
                        with builder.record(name="Momentum4D"):
                            spatial_momentum_map = {
                                "x": "px",
                                "y": "py",
                                "z": "pz",
                                "t": "e",
                            }
                            for key, value in spatial_momentum_map.items():
                                builder.field(key).real(getattr(particle, value))
                        for fname in particle.fieldnames:
                            if fname not in ["px", "py", "pz", "e"]:
                                builder.field(fname).real(getattr(particle, fname))
    return builder.snapshot()  # awkward array


class Particle:
    pass


class Event:
    pass


class EventInfo:
    pass



def to_awkward_nanoaod(event_iterable):
    """Convert iterable of LHEEvents to Awkward-Array using nanoAOD naming scheme."""

    from skhep.math import LorentzVector
    def p4(a):
        return LorentzVector(a.px, a.py, a.pz, a.e)

    genpart_field_map = {'pt':['p4.pt',float],'eta':['p4.eta',float],'genPartIdxMother':['mother1',int],'mass':['p4.mass',float],'pdgId':['id',int],'phi':['p4.phi',float],'status':['status',int]}
    
    builder = ak.ArrayBuilder()
    for event in event_iterable:
        with builder.record(name="Event"):
            builder.field("LHEWeight")
            with builder.record(name="LHEWeight"):
                builder.field("originalXWGTUP").real(event.eventinfo.weight)
            
            builder.field("LHEReweightingWeight")
            with builder.list():
                for k,v in event.weights.items():
                    with builder.record():
                        #don't store ids for now, since uproot won't save anyhting else than numpy dataypes (have to figure out how to convert it here or later.)
                        # builder.field("id").append(str(k))
                        builder.field("LHEReweightingWeight").append(float(v))
                        
                    
            builder.field('GenParts')
            with builder.list():
                for particle in event.particles:
                    with builder.record():
                        for fname,fattr_list in genpart_field_map.items():
                            fattr = fattr_list[0]
                            dtype = fattr_list[1]
                            attr = particle
                            for subattr_str in fattr.split('.'):
                                if(subattr_str == 'p4'):
                                    attr = p4(particle)
                                else:
                                    attr = getattr(attr,subattr_str)
                                if(callable(attr)):
                                    attr = attr()
                            builder.field(fname).append(dtype(attr))
    return builder.snapshot()
