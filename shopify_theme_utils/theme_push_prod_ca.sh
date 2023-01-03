clear

echo "*** publishing to new theme on prod ***"

cd ../shopify || exit

prod='gentlefawn-cad'

random_id=$(echo $RANDOM | md5sum | head -c 8)
theme_name_prefix="Psync_"

echo "$dynamic_theme_name"
dynamic_theme_name=$theme_name_prefix$random_id

shopify theme push --unpublished --theme="$dynamic_theme_name" --store $prod
echo "Push successful for: $dynamic_theme_name"
