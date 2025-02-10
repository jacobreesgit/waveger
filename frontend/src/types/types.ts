export interface AppleMusicInfo {
  attributes: {
    albumName: string
    artistName: string
    artwork: {
      width: number
      height: number
      url: string
      bgColor: string
      textColor1: string
    }
    releaseDate: string
    url: string
  }
}

export interface ChartSong {
  position: number
  name: string
  artist: string
  image: string
  peak_position: number
  weeks_on_chart: number
  url: string
  appleMusicInfo?: AppleMusicInfo
}
