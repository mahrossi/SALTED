import basis
import sys
sys.path.insert(0, './')
import inp
import numpy as np
from ase.io import read

def read_system(filename=inp.filename):
    
    # read species
    spelist = inp.species
    
    # read basis
    [lmax,nmax] = basis.basiset(inp.dfbasis)
    llist = []
    nlist = []
    for spe in spelist:
        llist.append(lmax[spe])
        for l in range(lmax[spe]+1):
            nlist.append(nmax[(spe,l)])
    nnmax = max(nlist)
    llmax = max(llist)
    
    # read system
    xyzfile = read(filename,":")
    ndata = len(xyzfile)
    
    #======================= system parameters
    atomic_symbols = []
    natoms = np.zeros(ndata,int) 
    for i in range(len(xyzfile)):
        atomic_symbols.append(xyzfile[i].get_chemical_symbols())
        natoms[i] = int(len(atomic_symbols[i]))
    natmax = max(natoms)

    return spelist, lmax, nmax, llmax, nnmax, ndata, atomic_symbols,natoms, natmax

def get_atom_idx(ndata,natoms,spelist,atomic_symbols):
    # initialize useful arrays
    atom_idx = {}
    natom_dict = {}
    for iconf in range(ndata):
        for spe in spelist:
            atom_idx[(iconf,spe)] = [] 
            natom_dict[(iconf,spe)] = 0
        for iat in range(natoms[iconf]):
            spe = atomic_symbols[iconf][iat]
            if spe in spelist:
               atom_idx[(iconf,spe)].append(iat)
               natom_dict[(iconf,spe)] += 1

    ########################################################################################

    natoms_total = 0
    natoms_list = []
    natoms = np.zeros(ndata,int)
    for iconf in range(ndata):
        # define relevant atoms
        natoms[iconf] = 0
        for spe in species:
            natoms[iconf] += natom_dict[(iconf,spe)]
        natoms_total += natoms[iconf]
        natoms_list.append(natoms[iconf])
        # Define relevant species
        excluded_species = []
        for iat in range(natoms[iconf]):
            spe = atomic_symbols[iconf][iat]
            if spe not in species:
                excluded_species.append(spe)
        excluded_species = set(excluded_species)
        for spe in excluded_species:
            atomic_symbols[iconf] = list(filter(lambda a: a != spe, atomic_symbols[iconf]))
    natmax = max(natoms_list)

    # recompute atomic indexes from new species selections
    atom_idx, natom_dict = get_atom_idx(ndata,natoms,species,atomic_symbols)

    #############################################################################

    return atom_idx,natom_dict

def get_conf_range(rank,size,ntest,testrangetot):
    if rank == 0:
        testrange = [[] for _ in range(size)]
        blocksize = int(ntest/float(size))
#       print(ntest,blocksize)
        if type(testrangetot) is not list: testrangetot = testrangetot.tolist()
        for i in range(size):
            if i == (size-1):
                rem = ntest - (i+1)*blocksize
#               print(i,(i+1)*blocksize,rem)
                if rem < 0:
                    testrange[i] = testrangetot[i*blocksize:ntest]
                else:
                    testrange[i] = testrangetot[i*blocksize:(i+1)*blocksize]
                    for j in range(rem):
                        testrange[j].append(testrangetot[(i+1)*blocksize+j])
            else:
                testrange[i] = testrangetot[i*blocksize:(i+1)*blocksize]
#           print(i,len(testrange[i]))
    else:
        testrange = None

    return testrange

