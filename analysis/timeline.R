require('ggplot2')

PATH = '/scratch/data/ec2_017/'

plot_convos = function(filename) {
  FLOWTIME = '/home/tierney/repos/web_perf/analysis/flowtime.rb'

  if (file.info(filename)[["size"]] == 0) {
    return()
  }
  
  data = read.csv(pipe(paste(FLOWTIME, filename)), header=T, sep=",")

  p = ggplot(data=data, aes(frame.time_relative, stream_id, color=direction)) + 
    geom_point(aes(size = frame.len),
               position=position_jitter(width=0, height=0.2)) + 
    scale_shape() +
    scale_x_continuous() + 
    scale_color_hue()
  out_svg = paste(filename, 'svg', sep='.')
  ggsave(out_svg)
  show(p)
}
#plot_convos('/scratch/data/ec2_017/2012-03-15-23-07-04_1cafda6b-2a66-464a-a563-86b4da6937cc_eu-west-1_verizon_firefox_80.client.pcap')
#plot_convos('/scratch/data/ec2_017/2012-03-15-21-45-42_92d35f4b-c14a-41f3-a15c-3c0df9c74d9b_us-east-1_wired_chrome_80.server.pcap')
#plot_convos('/scratch/data/ec2_017/2012-03-15-21-54-58_3c7abf89-6a84-4895-a330-aa2752da11b2_ap-southeast-1_wired_chrome_80.client.pcap')
plot_convos('test.pcap')
#for (filename in list.files(PATH, pattern='(tmobile|verizon).*.pcap$')) {
#  file_path = paste(PATH, filename, sep='')
#  plot_convos(file_path)
#}
