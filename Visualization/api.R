options("rgdal_show_exportToProj4_warnings"="none")
library(rgdal)
library(ggplot2)
library(sf)

# Import
ahn3_acqfile="Shapefiles/ahn3_measuretime.shp"
ahn3_acq_sp = readOGR(dsn=ahn3_acqfile)
ahn3_acq_sp_filt=ahn3_acq_sp[(ahn3_acq_sp@data$OBJECTID==5 | ahn3_acq_sp@data$OBJECTID==6 | ahn3_acq_sp@data$OBJECTID==11),]
ahn3_acq_sp_filt = st_as_sf(ahn3_acq_sp_filt)


#* @get /vishealth
function() {
  return('')
}


#' @post /plot 
#* @serializer png list(width = 600, height = 600, bg = "transparent")
function(df){
  
  data = df
  column_list <- list()
  for (inner_list in data) {
    # Transform the inner list to a column and append it to the column list
    column_list <- c(column_list, list(unlist(inner_list)))
  }
  presabs <- as.data.frame(column_list)
  
  # Set the column names
  colnames(presabs) <- names(data)
  mydata_clean2=presabs
  coordinates(mydata_clean2)=~x+y
  proj4string(mydata_clean2)<- CRS("+proj=sterea +lat_0=52.15616055555555 +lon_0=5.38763888888889 +k=0.9999079 +x_0=155000 +y_0=463000 +ellps=bessel +units=m +no_defs")
  mydata_clean= as(mydata_clean2, "data.frame")
  
  # Plot
  b = ggplot(ahn3_acq_sp_filt) + geom_sf() + geom_point(data = mydata_clean, 
    aes(x = x, y = y, color = probability), size = 1, alpha = 0.5
    ) + scale_color_gradient(low = "red", high = "green") + labs(
    x = 'X', y = 'Y', title = 'Habitat Locations of Great Reed Warbler', 
    subtitle = 'Presence Probability', caption = 'EPSG:28992') + theme_bw() + theme(
    legend.position = c(0.17, 0.8), legend.background = element_rect(fill = 
    "transparent"), plot.title = element_text(hjust = 0.5),
    plot.subtitle = element_text(hjust = 0.5),
    axis.title.y = element_text(angle = 0, vjust = 0.5))
  
  plot(b)
}