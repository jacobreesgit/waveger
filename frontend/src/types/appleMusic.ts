export interface AppleMusicAttributes {
  albumName: string
  artistName: string
  artwork: {
    url: string
    width: number
    height: number
    bgColor: string
    textColor1: string
    textColor2: string
    textColor3: string
    textColor4: string
  }
  composerName: string
  discNumber: number
  durationInMillis: number
  genreNames: string[]
  hasLyrics: boolean
  isAppleDigitalMaster: boolean
  isrc: string
  name: string
  playParams: {
    id: string
    kind: string
  }
  previews: Array<{ url: string }>
  releaseDate: string
  trackNumber: number
  url: string
}

export interface AppleMusicData {
  attributes: AppleMusicAttributes
  href: string
  id: string
  type: string
}
