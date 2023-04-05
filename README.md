# commit-freq

Displaying an amount of commits created by a user during a time period.

## Design


**Assumptions:**
- `user.name` and `user.email` are configured properly.

```plain
Milestone #1

Team: team-name
          Name (login) | Name (login)
Total
Average
-------
03/19 
03/20 
03/21 
03/22 
03/23 
03/24 
03/25 
03/26 
03/27 
03/28 
03/29 
03/30 
03/31 
04/01 
04/02 
04/03 
```

## Steps

1. Ask for information
   - milestone information
   - list of team slugs
   - github username to fullname mapping
2. Using team slug, get members
3. Filter out TAs' account.
4. For each user id in the team, get commit on main branch that are within the milestone
5. (todo) Filter out some types of commits (e.g. merge commit, commit that add PPTX file, or PDF file).
5. Use rich's UI to create table where row is date itemize of the dates in a milestone. Columns are the name of the member.

## Data Conversion

Flatten for `pd.DataFrame`

```plain
- committedDate
- author.user.login
```
