#! python3

import sys
from enum import Flag, auto


class Setting(Flag):
    NIL = 0
    IN_V = auto()
    IN_E = auto()
    IN_D10 = auto()
    IN_BV = auto()
    OUT_V = auto()
    OUT_E = auto()
    OUT_D10 = auto()
    OUT_BV = auto()
    NO_LOOP = auto()
    UNDIR = auto()
    SORT = auto()


def inputVertexList(lines):
    result = {}
    nV, *lines = lines
    try:
        nV = int(nV)
    except ValueError as e:
        if '\t' in e:
            print(
                "ERROR: tried to open file with mode -v. Maybe you meant -e?")

    assert nV == len(lines),\
        f"Wrong number of lines in file. Expected {nV}, found {len(lines)}"

    for i in range(nV):
        line = lines[i]
        edges = line.split(":")
        v, edges = edges
        edges = edges.strip().split(' ')

        # edges = line.strip().split(' ')
        # v = i
        assert edges[-1] == '#', "Last element of line expected to be '#'"
        edges = edges[:-1]
        if str(v) in result.keys():
            raise ValueError("Declared twice vertex " + v)
        result[str(v)] = list(map(int, edges))

    # Correction for empty nodes not present
    # correction = []
    # for edges in result.values():
    #     for w in edges:
    #         if str(w) not in indexmap:
    #             correction.append(str(w))

    # for w in correction:
    #     if w not in result.keys():
    #         result[w] = []
    #     if w not in indexmap:
    #         indexmap[w] = nV
    #         nV += 1

    return result


def inputEdgeList(lines):
    result = {}
    i = -1
    nV = 0
    nE = 0

    for line in lines:
        # Skip comments
        if line[0].strip() == '%':
            continue

        v, w, *_ = line.strip().split()

        # First line with graph dimentions
        if i < 0:
            nV, nE = list(map(int, [v, w, *_]))[1:]
            i += 1
            continue

        if str(v) not in result:
            result[str(v)] = [int(w)]
            i += 1
        else:
            result[str(v)].append(int(w))

        if str(w) not in result:
            result[str(w)] = []
            i += 1

    # Create isolated vertexes
    while i < nV:
        result[str(-i)] = []
        i += 1

    return result


def inputDimacs10(lines):
    result = {}
    i = 1

    header, *lines = lines
    nV, *_ = [int(n) for n in header.split()]

    for line in lines:
        assert i <= nV, f"Too many lines. Expected {nV}, found at least {i}"
        result[str(i)] = list(map(int, line.split()))
        i += 1

    return result


def inputBinaryVertex(chunk, result={}):
    v = None

    for j in range(0, len(chunk), 8):
        w = int.from_bytes(chunk[j:j + 8], byteorder="little", signed=True)

        if j == 0:
            assert w >= 0, f'Expected positive value, found {w}'

            v = str(w)
            result[v] = []
        else:
            if w < 0:
                break
            result[v].append(w)

    return result


def removeLoops(nodeList):
    for v, edges in nodeList.items():
        try:
            edges.remove(int(v))
        except ValueError:
            continue

    return nodeList


def checkUndir(nodeList):
    missing = {}

    for v, edges in nodeList.items():
        for w in edges:
            try:
                if int(v) not in nodeList[str(w)]:
                    if len(missing) == 0:
                        print("INFO: Found direct edge in graph.")
                        print("Preparing correction data...")

                    if str(w) in missing:
                        missing[str(w)].append(int(v))
                    else:
                        missing[str(w)] = [int(v)]
            except KeyError:
                if str(w) not in missing:
                    if len(missing) == 0:
                        print("INFO: Found direct edge in graph.")
                        print("Preparing correction data...")

                    if str(w) in missing:
                        missing[str(w)].append(int(v))
                    else:
                        missing[str(w)] = [int(v)]

    if len(missing) > 0:
        print("Correction data is ready!")
        print("Correcting directness...")

        for key, value in missing.items():
            if key in nodeList:
                nodeList[str(key)].extend(value)
            else:
                nodeList[str(key)] = value

        print("Directness correction complete!")

    return nodeList


def ouputVertexList(nodeList, doSort):
    skew = min(map(lambda i: int(i[0]), nodeList.items()))
    return f"{len(nodeList)}\n" + '\n'.join([
        f"{int(v) - skew}: " \
            + ' '.join([
                str(e - skew) for e in
                    (sorted(edges, \
                    key=lambda e: int(e)) if doSort \
                    else edges)
                ])
            + " #"
        for v, edges in
            (sorted(nodeList.items(), \
                key=lambda i: int(i[0])) if doSort \
                else nodeList.items())
    ])


def ouputEdgeList(nodeList, doSort):
    skew = min(map(lambda i: int(i[0]), nodeList.items()))
    return f"{sum(map(len, nodeList.values()))}\t{len(nodeList)}\n" + '\n'.join([
        '\n'.join([
            f"{str(v - skew)}\t{str(w - skew)}"
            for w in
                (sorted(edges, \
                    key=lambda e: int(e)) if doSort \
                    else edges)
        ])
        for v, edges in
            (sorted(nodeList.items(), \
                key=lambda i: int(i[0])) if doSort \
                else nodeList.items())
    ])


def ouputDimacs10(nodeList, doSort):
    nV = len(nodeList)
    # DIMACS10 uses 1-based node indexing
    skew = min(map(lambda i: int(i[0]), nodeList.items())) + 1
    # Conted only one way undirected edges
    nE = int(sum([len(edges) for _, edges in nodeList.items()]) / 2)
    return f"{nV} {nE}\n" + '\n'.join([
        ' '.join([
            str(e - skew) for e in
                (sorted(edges, \
                key=lambda e: int(e)) if doSort \
                else edges)
            ])
        for _, edges in
            (sorted(nodeList.items(), \
                key=lambda i: int(i[0])) if doSort \
                else nodeList.items())
    ])


def outputBinaryVertex(nodeList, doSort, pad=-1):
    nEmax = len(max(nodeList.values(), key=len))
    output = list(len(nodeList).to_bytes(8, 'little', signed=True)) + \
            list(nEmax.to_bytes(8, 'little', signed=True))

    skew = min(map(lambda i: int(i[0]), nodeList.items()))
    for v, edges in (sorted(nodeList.items(), \
                        key=lambda i: int(i[0])) if doSort \
                        else nodeList.items()):
        output += list((int(v) - skew).to_bytes(8, 'little', signed=True))
        edges = (sorted(edges, \
                    key=lambda e: int(e)) if doSort \
                    else edges)
        for w in (edges + [pad] * (nEmax - len(edges))):
            outW = -1 if int(w) == -1 else int(w) - skew
            output += list(outW.to_bytes(8, 'little', signed=True))
            yield bytearray(output)
            output = []


def convert(inF, outF, settings):
    nodes = {}

    print(f"Loading {inF}...")

    assert len(Setting) == 12, "Exhaustive Setting definition"
    if settings & Setting.IN_E:
        with open(inF, 'r') as f:
            nodes = inputEdgeList(f.readlines())
    elif settings & Setting.IN_V:
        with open(inF, 'r') as f:
            nodes = inputVertexList(f.readlines())
    elif settings & Setting.IN_D10:
        with open(inF, 'r') as f:
            nodes = inputDimacs10(f.readlines())
    elif settings & Setting.IN_BV:
        with open(inF, 'rb') as f:
            nV = int.from_bytes(f.read(8), byteorder='little', signed=True)
            nEmax = int.from_bytes(f.read(8), byteorder='little', signed=True)
            for _ in range(nV):
                nodes = inputBinaryVertex(f.read(8 * (1 + nEmax)), nodes)
    else:
        print(f"ERROR: inMode not specified")
        sys.exit(1)

    print("Loading complete!")
    print(f"V: {len(nodes)}, E: {sum(map(len, nodes.values()))}")

    assert len(Setting) == 12, "Exhaustive Setting definition"
    if settings & Setting.NO_LOOP:
        print("Removing looping edges...")
        nodes = removeLoops(nodes)
        print("Looping edges removed!")
        print(f"V: {len(nodes)}, E: {sum(map(len, nodes.values()))}")

    if settings & Setting.UNDIR:
        print("Checking graph for direct edges...")
        nodes = checkUndir(nodes)
        print("Graph is undirected!")
        print(f"V: {len(nodes)}, E: {sum(map(len, nodes.values()))}")

    print(f"Writing output file {outF}...")

    assert len(Setting) == 12, "Exhaustive Setting definition"
    if settings & Setting.OUT_E:
        with open(outF, 'w') as f:
            f.write(ouputEdgeList(nodes, settings & Setting.SORT))
    elif settings & Setting.OUT_V:
        with open(outF, 'w') as f:
            f.write(ouputVertexList(nodes, settings & Setting.SORT))
    elif settings & Setting.OUT_D10:
        with open(outF, 'w') as f:
            f.write(ouputDimacs10(nodes, settings & Setting.SORT))
    elif settings & Setting.OUT_BV:
        with open(outF, 'wb') as f:
            for b in outputBinaryVertex(nodes, settings & Setting.SORT):
                f.write(b)
    else:
        print(f"ERROR: outMode not specified")
        sys.exit(1)

    print("Writing completed!")


def extractArg(args):
    if len(args) > 0:
        return args[0], args[1:]
    else:
        raise IndexError()


def printUsage():
    assert len(Setting) == 12, "Exhaustive Setting definition"
    print("Usage:")
    print(f"{sys.argv[0]} [CMD] | [MODE <graph_in> MODE <graph_out> OPT]")
    print("CMD:")
    print("\t-h\tPrint this message")
    print("MODE:")
    print("\t-v\tThe file is interpreted as a list of verteces")
    print("\t-e\tThe file is interpreted as a list of edges (quasi-matrix market)")
    print(
        "\t-d10\tThe file is interpreted as part of the 10th DIMACS challenge")
    print("\t-bv\tThe file is interpreted as binary list of vertices")
    print("OPT:")
    print("\t-l\tDeletes self-looping edges")
    print("\t-u\tForce the output graph to be undirected")
    print("\t-s\tSort output ascending")


def main(args):
    settings = Setting.NIL
    inFile = None
    outFile = None

    assert len(Setting) == 12, "Exhaustive Setting definition"
    while len(args) > 0:
        arg, args = extractArg(args)

        if arg == '-h':
            printUsage()
            sys.exit(0)
        elif arg == '-v':
            try:
                filename, args = extractArg(args)
            except IndexError:
                printUsage()
                sys.exit(0)

            if inFile == None:
                settings |= Setting.IN_V
                inFile = filename
            else:
                settings |= Setting.OUT_V
                outFile = filename
        elif arg == '-e':
            try:
                filename, args = extractArg(args)
            except KeyError:
                printUsage()
                sys.exit(0)

            if inFile == None:
                settings |= Setting.IN_E
                inFile = filename
            else:
                settings |= Setting.OUT_E
                outFile = filename
        elif arg == '-d10':
            try:
                filename, args = extractArg(args)
            except KeyError:
                printUsage()
                sys.exit(0)

            if inFile == None:
                settings |= Setting.IN_D10
                inFile = filename
            else:
                settings |= Setting.OUT_D10
                outFile = filename
        elif arg == '-bv':
            try:
                filename, args = extractArg(args)
            except KeyError:
                printUsage()
                sys.exit(0)

            if inFile == None:
                settings |= Setting.IN_BV
                inFile = filename
            else:
                settings |= Setting.OUT_BV
                outFile = filename
        elif arg == '-l':
            settings |= Setting.NO_LOOP
        elif arg == '-u':
            settings |= Setting.UNDIR
        elif arg == '-s':
            settings |= Setting.SORT
        else:
            print(f"WARNING: Unrecognized parameter '{arg}' is being skipped.")

    if inFile != None and outFile != None:
        convert(inFile, outFile, settings)
    else:
        printUsage()
        sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
    print("DONE")
