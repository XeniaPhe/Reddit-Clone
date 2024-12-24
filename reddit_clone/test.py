filter = "joinDate_Exact"
filter_parts = filter.split('_')[1:]
filter_operator = '_'.join(filter_parts).lower()
print(filter_operator)