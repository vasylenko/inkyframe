resource "aws_resourceexplorer2_view" "inkyframe" {
  name = local.project_name
  filters {
    filter_string = "tag.key:project-name tag.value:${local.project_name}"
  }
  included_property {
    name = "tags"
  }
}

resource "aws_resourcegroups_group" "inkyframe" {
  name = local.project_name
  resource_query {
    query = jsonencode({
      ResourceTypeFilters = ["AWS::AllSupported"],
      TagFilters = [
        {
          Key    = "project-name",
          Values = [local.project_name]
        }
      ]
    })
    type = "TAG_FILTERS_1_0"
  }
}