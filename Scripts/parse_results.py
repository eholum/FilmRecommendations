import csv
import sys

args = sys.argv
if (len(args) <=2):
    print("Missing Required Arguments: REVIEWS_FILE OUTPUT_FILE")
    sys.exit(1)
    

# Reviews file
reviews_file = args[1]

# Output file
output_file = args[2]


#####
#
# Load reviews and titles
#
#####
reviews = {}
titles = {}
mids = set()

with open(reviews_file, newline='\n') as f:
    reader = csv.reader(f, delimiter='\t', quotechar='\"')
    
    for row in reader:
        name = row[0]
        mid = int(row[1])
        title = row[2]
        score = row[6]
        
        titles[mid] = title
        
        if name not in reviews:
            reviews[name] = {}
            
        reviews[name][mid] = score
        
        mids.add(mid)


f = open(output_file, 'w')
f.write('reviewer\t')
f.write('\t'.join([titles[i] for i in sorted(mids)]))
f.write('\n')

for name in reviews:
    f.write(name + '\t')
    
    for mid in sorted(mids):
        if mid in reviews[name]:
            f.write(reviews[name][mid])
        else:
            f.write('NA')
        f.write('\t')
   
    f.write('\n')
    
f.close()