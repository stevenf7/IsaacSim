# This is the script used to create the shapenet_db2.pickle.bz2 file.
import glob
import csv

path = r"F:\shapenet\ShapeNetCorev1"
csv_files = glob.glob(path + "/*.csv")

snDb = {}
for filename in csv_files:
    synsetId = filename[-12:-4]

    with open(filename, encoding="utf8") as csv_file:
        readCSV = csv.reader(csv_file, delimiter=",")
        skipFirst = True
        synsetDb = {}
        for row in readCSV:
            if skipFirst:
                skipFirst = False
                continue
            modelId = row[0]
            modelDb = modelId[: modelId.find(".")]
            modelId = modelId[modelId.find(".") + 1 :]

            wnsynset = row[1]
            wnlemmas = row[2]
            up = row[3]
            front = row[4]
            name = row[5]
            tags = row[6]

            synsetDb[modelId] = (wnsynset, wnlemmas, up, front, name, tags)
        snDb[synsetId] = synsetDb

import bz2

try:
    import cPickle as pickle
except:
    import pickle
sfile = bz2.BZ2File("shapenet_db2.pickle.bz2", "wb")
pickle.dump(snDb, sfile)
sfile.close()
f = bz2.BZ2File("shapenet_db2.pickle.bz2", "rb")

new_dict = pickle.load(f)
f.close()
print(len(new_dict))
