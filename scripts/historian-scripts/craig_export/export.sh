TOPICID="$1"
DATABASE="$2"
echo $TOPICID
echo $DATABASE

OUTFILE="$DATABASE-$TOPICID.csv"
#echo $OUTFILE
#touch $OUTFILE
QUERY="{ topic_id: ObjectId(\"$TOPICID\")}"
echo $QUERY
mongoexport -u reader -p volttronReader -h vc-db.pnl.gov \
            -d "$DATABASE" --authenticationDatabase "$DATABASE" -c data \
            -q "$QUERY" \
            --sort '{ts: 1}' --type=csv --out "$OUTFILE" --fields topic_id,ts,value