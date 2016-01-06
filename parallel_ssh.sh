#/bin/bash

nodes="big_list_of_nodes.txt"
counter=0
cmd="uptime"

while read node; do
    # Everything between () runs in parallel in the backgroup
    (output=`ssh -o ConnectTimeout=5 $node $cmd 2>&1`

    if [ $? -eq 0 ]; then
       echo "$node: $output"
    else
       echo "Connection timeout for node $node"
    fi) &
    # Parallel processing ends here

    let counter+=1

    # Do 10 nodes at a time

    if [ $counter -eq 10 ]; then
       wait
       counter=0
    fi

done < $nodes
