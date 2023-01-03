clear

echo "*** publishing to new theme on dev ***"

cd ../shopify || exit

dev='gentlefawn-dev'

random_id=$(echo $RANDOM | md5sum | head -c 8)
theme_name_prefix="Psync_"

echo "$dynamic_theme_name"
dynamic_theme_name=$theme_name_prefix$random_id

shopify theme push --unpublished --theme="$dynamic_theme_name" --store $dev
echo "Publishing: $dynamic_theme_name"
shopify theme publish
