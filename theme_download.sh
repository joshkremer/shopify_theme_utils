live_us='gentlefawn-usd'
staging_ca='gentlefawn-staging-ca'

shopify login --store $live_us

shopify theme pull --live

shopify switch --store $staging_ca

shopify theme push --unpublished

shopify theme publish
