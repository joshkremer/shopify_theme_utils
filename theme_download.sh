staging_us='gentlefawn-staging-us'
staging_ca='gentlefawn-staging-ca'

shopify login --store $staging_us

shopify theme pull --live

shopify switch --store $staging_ca

shopify theme push --unpublished

shopify theme publish
