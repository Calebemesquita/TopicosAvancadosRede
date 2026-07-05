# Templates

- `interfaces.j2`: loopback e enderecos das interfaces.
- `bgp.j2`: ASN, router-id, neighbors, MD5, TTL security e address-family.
- `access_lists.j2`: prefix-lists e community-lists.
- `route_maps.j2`: AS-PATH prepend, local-preference, bogons e communities.
- `frr_bgp.j2`: template principal que inclui os demais blocos.
