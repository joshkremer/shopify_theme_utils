live_us='gentlefawn-usd'
dev='gentlefawn-dev'
random_id=$(echo $RANDOM | md5sum | head -c 8)
theme_name_prefix="Psync_"
#date=$(date '+%Y-%m-%d %H:%M:%S')
theme_list_filename="theme_list.txt"
echo "$dynamic_theme_name"
shopify login --store $live_us
shopify theme list > $theme_list_filename

# look for [live], get id
filename=$theme_list_filename
n=1

while read line; do
if [[ "$line" == *"[live]"* ]]; then
  # strip using space after id
  rough_id=$(echo "$line" | cut -d " " -f 1)
  live_theme_name=$line
  # strip using hashn
  live_theme_id=$(echo "$rough_id" | cut -d "#" -f 2)

  echo "#theme_id: $live_theme_id"
fi
n=$((n+1))
done < $filename

dynamic_theme_name=$theme_name_prefix$random_id"___"$live_theme_id
shopify theme pull --live
shopify switch --store $dev
shopify theme push --unpublished --theme="$dynamic_theme_name"
shopify theme publish
