| Prompt | Building type | Requested | Produced | Quality | Warnings | MUST adj | Runtime (ms) | Deterministic |
|---|---|---|---|---|---|---|---|---|
| house | family_home | 9 | 9 | 75 | 2 | n/a | 22 | True |
| clinic | clinic | 8 | 10 | 87 | 3 | n/a | 9 | True |
| office | office | 9 | 10 | 79 | 3 | 67% | 10 | True |
| restaurant | restaurant | 8 | 9 | 51 | 5 | n/a | 6 | True |
| two_floor_house | family_home | 10 | 10 | 77 | 3 | n/a | 8 | True |
| accessible_home | family_home | 6 | 6 | 82 | 3 | n/a | 6 | True |

Warning detail:
- [house] Rooms outside expected size ranges: Kitchen, Open Plan Living, Bedroom 1, Bedroom 2, Bathroom 1, Master Bedroom, Bathroom 2
- [house] Avoid-adjacency violations: Kitchen next to Bedroom
- [clinic] Rooms outside expected size ranges: Hallway
- [clinic] Preferred adjacency not met: Bathroom near Waiting Room, Waiting Room near Consultation Room
- [clinic] Clinic flow issues: waiting near consultation
- [office] Rooms outside expected size ranges: Entry, Reception, Office, Bathroom 2
- [office] Preferred adjacency not met: Kitchen near Storage, Storage near Workspace
- [office] Avoid-adjacency violations: Bathroom next to Kitchen
- [restaurant] Rooms outside expected size ranges: Entry, Reception, Dining Room, Bar, Bathroom 1, Bathroom 2
- [restaurant] Preferred adjacency not met: Bathroom near Dining Room, Dining Room near Kitchen, Kitchen near Storage
- [restaurant] Avoid-adjacency violations: Bathroom next to Kitchen
- [restaurant] Restaurant kitchen is too close to the public entry
- [restaurant] Low adjacency satisfaction: 25% of preferred pairs met
- [two_floor_house] Rooms outside expected size ranges: Bedroom 1, Bedroom 2, Bedroom 3
- [two_floor_house] Preferred adjacency not met: Dining Room near Living Room, Kitchen near Living Room
- [two_floor_house] Avoid-adjacency violations: Kitchen next to Bedroom, Master Bedroom next to Kitchen
- [accessible_home] Rooms outside expected size ranges: Open Plan Living, Bathroom
- [accessible_home] Preferred adjacency not met: Bathroom near Bedroom
- [accessible_home] Avoid-adjacency violations: Kitchen next to Bedroom, Master Bedroom next to Kitchen
