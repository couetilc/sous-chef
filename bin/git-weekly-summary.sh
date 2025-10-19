usage="
Usage: ./git-weekly-summary <author>

Prints out the past week of your git history in the sous-chef repository
"
author="$1"

if [ -z "$author" ]; then
	echo "Error: must specify and author"
	echo "$usage"
	exit 1
fi

TZ=America/New_York git log \
	--all \
	--since="1 week ago" \
	--date=format-local:"%Y-%m-%d %H:%M:%S" \
	--format="%ad %h %s" \
	--author="$author" \
	--no-merges
